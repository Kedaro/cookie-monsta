from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException, NoSuchWindowException
from selenium.webdriver.chrome.options import Options  
from ._utilities import cookie_count_text_to_float, BuildingInfo, PurchaseStrategy
from ._config import INITIAL_CPS_BUILDINGS
import time
import re
import logging
import os


# TODO: log cps over time. Build tools to plot and compare

SITE_URL = "https://orteil.dashnet.org/cookieclicker/"
UPGRADE_PATH = '//*[@id=\"upgrade0\"]'
COOKIE_COUNT_PATH = '//*[@id=\"cookies\"]'
COOKIE_PATH = '//*[@id=\"bigCookie\"]'
# estimated based on emprical evidence
CLICKS_PER_SECOND = 28

MAX_BUILING_INDEX = max(INITIAL_CPS_BUILDINGS, key=int)

logger = logging.getLogger(__name__)


class CookieClicker(object):
    def __init__(self, chrome_driver_path: str, purchase_strategy: int, absolute_save_path:str):
        
        chrome_options = Options() 
        if absolute_save_path:
            save_path = os.path.abspath(absolute_save_path)+"/ChromeProfile"
            logger.info(f"Game progress will be saved and loaded from {save_path}")
            chrome_options.add_argument(f"--user-data-dir={save_path}")
        else:
            logger.warning("No save path provided, game progress will not be saved.")
        
        self.driver = webdriver.Chrome(chrome_driver_path, options=chrome_options) 
        
        try:
            self.purchase_strategy = PurchaseStrategy(purchase_strategy)
        except ValueError:
            valid_str = [f"{e.value}: {e.name}" for e in PurchaseStrategy]
            logger.exception(f"Invalid purchase strategy. Valid number ars {valid_str}. See README for more info.")
            exit(1)

        logger.info(f"Running using {self.purchase_strategy.name}: {self.purchase_strategy.value} purchase strategy.")

        self.cookie = None
        self.upgrade = None

        self.building_info_store = {0: BuildingInfo(cost=15, cps=INITIAL_CPS_BUILDINGS[0])} # initial cost of cookie divided by initial cps

        self.loops_since_cps_update = 0

    def run(self):

        self.start_up()

        while True:

            try:
                self.tick()

            except NoSuchWindowException:
                logger.exception("Window not found.", exc_info=True)
                raise
            # other selenium exception 
            except WebDriverException:
                logger.exception("Issue with selenium. Trying to continue looping.", exc_info=True)
            # parsing error
            except AssertionError:
                logger.exception("Assertion failed. Trying to continue looping.", exc_info=True)
            except ValueError:
                logger.exception("Issue parsing. Trying to continue looping.", exc_info=True)
            # all other exceptions should raise 
            except Exception:
                raise
    
    def start_up(self):
        self.driver.get(SITE_URL)
        
        # TODO: Use better method than sleep
        # sleep to load
        time.sleep(4)
        self.cookie = self.driver.find_element_by_xpath(COOKIE_PATH)

    def tick(self):
        self.loops_since_cps_update += 1

        for _ in range(CLICKS_PER_SECOND*2):
            self.cookie.click()

        logger.info(f"Current CPS: {self.get_current_production_cps()}")
        
        self.click_golden_cookie_if_possible()
        self.purchase_upgrade_if_possible()

        # Force a cps update every 10 cycles
        if self.loops_since_cps_update > 10 :
            self.loop_index = 0
            self.update_building_info(update_cps=True)

        # most efficient building key
        best_building = self.get_best_building_to_purchase()
        # check if available
        product = self.driver.find_element_by_xpath(f"//*[@id=\"product{best_building}\"]")
        if product.get_attribute("class") == "product unlocked enabled":
            # purchase
            self._click_non_upgrade_product(product)
        # otherwise wait to buy
        else:
            logger.debug(f"Waiting to buy product {best_building}")
            pass
    
    def get_best_building_to_purchase(self) -> int:
        # TODO: implement various startegies
        if self.purchase_strategy == PurchaseStrategy.MIN_COST_PER_CPS:
            return self._min_cost_per_csp()
        if self.purchase_strategy == PurchaseStrategy.WEIGHTED_COST_PER_CPS:
            return self._weighted_min_cost_per_csp()
        else:
            raise NotImplementedError(f"Purchase strategy for {self.purchase_strategy.value}: {self.purchase_strategy.name} not implemented.")
    
    def _min_cost_per_csp(self) -> float:
        def loss(key_element):
            return self.building_info_store[key_element].cost/self.building_info_store[key_element].cps

        return min(self.building_info_store, key=(lambda key_element: loss(key_element)))

    def _weighted_min_cost_per_csp(self) -> float:
        def loss(current_cps: float, key_element: int):
            cost = self.building_info_store[key_element].cost
            delta_cps = self.building_info_store[key_element].cps
            if current_cps != 0:
                val = 1.15 * (cost/current_cps) + (cost/delta_cps)
            else:
                val = cost/delta_cps
            
            return val
        
        curr_cps = self.get_current_production_cps()

        return min(self.building_info_store, key=(lambda key_element: loss(curr_cps, key_element)))
        
    
    def get_cost_and_cps_building(self, building_num: int) -> (float, float):
        """
        returns cost, cps
        """
        
        while True:
            failed = False

            action = ActionChains(self.driver)

            parent_level_menu = self.driver.find_element_by_xpath(f"//*[@id=\"product{building_num}\"]") 
            action.move_to_element(parent_level_menu).perform()

            tooltip = self.driver.find_element_by_xpath(f"//*[@id=\"tooltip\"]")
            tooltip_text = tooltip.text

            price_obj = self.driver.find_element_by_xpath(f"//*[@id=\"productPrice{building_num}\"]")
            
            # set initial values
            cost = cookie_count_text_to_float(price_obj.text)
            cps = 0

            lines = tooltip_text.splitlines()

            # parse tootip text
            if len(lines) > 5:
                tool_tip_cost = cookie_count_text_to_float(lines[0])
                
                # there is an issue with getting the tooltip data, sometimes returns values for wrong item
                # this comparison will not work if they coicedentally cost the same (v. unlikely)
                if int(tool_tip_cost) != int(cost):
                    logger.warning(f"Failed to get correct info for Building {building_num}. Acutal cost {cost}, tooltip cost {tool_tip_cost} ")
                    failed = True

                cps_text = lines[4]
                cps_text = re.sub(r'^\D*', "", cps_text)
                cps_text = cps_text.strip(" cookies per second")
                cps = cookie_count_text_to_float(cps_text)
            else:            
                logger.debug("Using initial cps value")
                cps = INITIAL_CPS_BUILDINGS[building_num]

            if not failed:
                return cost, cps

    def quick_get_cost_building(self, building_num: int) -> float:
        price_obj = self.driver.find_element_by_xpath(f"//*[@id=\"productPrice{building_num}\"]")
        return cookie_count_text_to_float(price_obj.text)

    def update_building_info(self, update_cps):
        """
        Must be called anytime an action is taken that could change the cost/cps
        """
        if update_cps:
            logger.debug("Updating CPS")
        
        purchase_product_num = 0
        while purchase_product_num <= MAX_BUILING_INDEX: 
            # check if product is unlocked
            product = self.driver.find_element_by_xpath(f"//*[@id=\"product{purchase_product_num}\"]")            
            if product.get_attribute("class") in ("product unlocked enabled", "product unlocked disabled"):
                if update_cps:
                    cost, cps = self.get_cost_and_cps_building(purchase_product_num) 
                    self.building_info_store[purchase_product_num] = BuildingInfo(cost=cost, cps=cps)
                else:
                    cost = self.quick_get_cost_building(purchase_product_num)
                    if purchase_product_num in self.building_info_store:
                        self.building_info_store[purchase_product_num].cost = cost
                    else:
                        self.building_info_store[purchase_product_num] = BuildingInfo(cost=cost, cps=INITIAL_CPS_BUILDINGS[purchase_product_num])

                purchase_product_num += 1
                continue
            # if still locked, ignore it and the rest (because unlocked sequentially)
            break
        
        if update_cps:
            self.loops_since_cps_update = 0  
    
    def click_golden_cookie_if_possible(self) -> bool:
            clicked = False
            try:
                golden_cookies_children = self.driver.find_element_by_xpath("//*[@id=\"goldenCookie\"]").find_elements_by_xpath(".//*")
                shimmers_children = self.driver.find_element_by_xpath("//*[@id=\"shimmers\"]").find_elements_by_xpath(".//*")
                
                # TODO: add seasons popup

                # check if populated
                if len(golden_cookies_children) > 0:
                    child = golden_cookies_children[0]
                    logger.debug("About to click golden cookie child")
                    self._click_non_upgrade_product(child)
                    logger.debug("Clicked golden cookie")
                    clicked = True
                if len(shimmers_children) > 0:
                    child = shimmers_children[0]
                    logger.debug("About to click  shimers child child")
                    self._click_non_upgrade_product(child)
                    logger.debug("Clicked shimers child")
                    clicked = True
            except:
                logger.error("Failed to click bonus")
            finally:
                return clicked

    def _click_upgrade_product(self, selenium_object, description=None):
        selenium_object.click()
        logger.debug(f"Clicking upgrade: {description}")
        self.update_building_info(update_cps=True)


    def _click_non_upgrade_product(self, selenium_object, description=None):
        selenium_object.click()
        logger.debug(f"Clicking non upgrade, non cookie: {description}")
        self.update_building_info(update_cps=False)      
    
    def purchase_upgrade_if_possible(self):
        clicked = False
        try:
            # define only if not defined
            if self.upgrade is None:
                self.upgrade = self.driver.find_element_by_xpath(UPGRADE_PATH)
            #try to click if you can
            if self.upgrade.get_attribute("class") == "crate upgrade enabled":
                logger.debug("Buying upgrade")
                self._click_upgrade_product(self.upgrade)
                self.upgrade = None
                clicked = True
        except Exception as _:
            self.upgrade = None
            logger.debug("No upgrade available")
        finally:
            return clicked


    def get_cookie_count(self) -> float:
        cookies = self.driver.find_element_by_xpath(COOKIE_COUNT_PATH)
        txt = cookies.text
        # split from new line on
        lines = txt.split('\n')
        # remove cookies word
        txt_count = lines[0]
        txt_count = txt_count.strip(" cookies")
        # remove commas
        txt_count = txt_count.strip(",")
        return cookie_count_text_to_float(txt_count)

    def get_current_production_cps(self) -> float:
        try:
            cookies = self.driver.find_element_by_xpath(COOKIE_COUNT_PATH)
            txt = cookies.text
            # split from new line on
            lines = txt.split('\n')
            # remove cookies word
            txt_cps = lines[-1]
            txt_cps = re.sub(r'^\D*', "", txt_cps)
            # remove commas
            txt_cps = txt_cps.strip(",")
            return cookie_count_text_to_float(txt_cps)
        except Exception:
            logger.exception(f"Failed to parse {lines}")
            raise

    def clean_up(self):
        try:
            logger.error("Cleaning up.")
            self.driver.quit()
        except Exception:
            logger.exception("Unable to clean up.", exc_info=True)





