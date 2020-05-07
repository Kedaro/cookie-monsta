from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from count_cookies import cookie_count_text_to_float
from config import INITIAL_CPS_BUILDINGS
import time
import re
import logging
from dataclasses import dataclass


# TODO: instead of min cost/cps use this algo (1.15*(cost/cps) + cost/delta(cps)) https://cookieclicker.fandom.com/wiki/Frozen_Cookies_%28JavaScript_Add-on%29#Efficiency.3F_What.27s_that.3F
# TODO: configurable strategy (greedy, discount future)
# TODO: log cps over time. Build tools to plot and compare 
# TODO: find most efficient solution to tooltip issue

CHROME_DRIVER_PATH = "/home/syd/Desktop/utilities/chromedriver_linux64/chromedriver" 
SITE_URL = "https://orteil.dashnet.org/cookieclicker/"
UPGRADE_PATH = '//*[@id=\"upgrade0\"]'
COOKIE_COUNT_PATH = '//*[@id=\"cookies\"]'
COOKIE_PATH = '//*[@id=\"bigCookie\"]'
# estimated based on emprical evidence
CLICKS_PER_SECOND = 28

MAX_BUILING_INDEX = max(INITIAL_CPS_BUILDINGS, key=int)

logger = logging.getLogger('clicker')
logger.setLevel(logging.INFO)


@dataclass
class BuildingInfo:
    cost: float
    cps: float



class CookieClicker(object):
    def __init__(self):
        self.driver = webdriver.Chrome(CHROME_DRIVER_PATH) 
        self.cookie = None
        self.upgrade = None

        self.building_info_store = {0: BuildingInfo(cost=15, cps=INITIAL_CPS_BUILDINGS[0])} # initial cost of cookie divided by initial cps

        self.loops_since_cps_update = 0

    def run(self):
        self.driver.get(SITE_URL)
        # sleep to load
        time.sleep(2)
        self.cookie = self.driver.find_element_by_xpath(COOKIE_PATH)

        while True:
            self.loops_since_cps_update += 1

            for _ in range(CLICKS_PER_SECOND*2):
                self.cookie.click()
            
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
        min_val = None
        min_index = 0
        for (index, info) in self.building_info_store.items():
            cost_per_cps = info.cost/info.cps
            logger.debug(f"Building {index}: Cost/cps: {cost_per_cps} Cost:{info.cost} CPS: {info.cps}")
            if (min_val is None) or (min_val > cost_per_cps):
                min_val = cost_per_cps
                min_index = index
        return min_index

    
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
                if tool_tip_cost != cost:
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
        use the update_cost_cps_decorator

        update_cps is optional becuase it takes along time and only need to be done when upgrade is bought
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

    def _click_upgrade_product(self, selenium_object, description=None):
        selenium_object.click()
        logger.debug(f"Clicking upgrade: {description}")
        self.update_building_info(update_cps=True)


    def _click_non_upgrade_product(self, selenium_object, description=None):
        selenium_object.click()
        logger.debug(f"Clicking non upgrade, non cookie: {description}")
        self.update_building_info(update_cps=False)        
    
    def click_golden_cookie_if_possible(self) -> bool:
            clicked = False
            try:
                golden_cookies_children = self.driver.find_element_by_xpath("//*[@id=\"goldenCookie\"]").find_elements_by_xpath(".//*")
                shimmers_children = self.driver.find_element_by_xpath("//*[@id=\"shimmers\"]").find_elements_by_xpath(".//*")
                
                # TODO: add seasons popup

                # check if populated
                if len(golden_cookies_children) > 0:
                    child = golden_cookies_children[0]
                    logger.info("About to click golden cookie child")
                    self._click_non_upgrade_product(child)
                    logger.info("Clicked golden cookie")
                    clicked = True
                if len(shimmers_children) > 0:
                    child = shimmers_children[0]
                    logger.info("About to click  shimers child child")
                    self._click_non_upgrade_product(child)
                    logger.info("Clicked shimers child")
                    clicked = True
            except:
                logger.error("Failed to click bonus")
            finally:
                return clicked
    
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
        # remove from new line on
        txt_count = re.sub(r'\s.*$', "", txt)
        # remove cookies label
        txt_count = txt_count.strip(" cookies")
        # remove and commas
        txt_count = txt_count.strip(",")
        return cookie_count_text_to_float(txt_count)

    def clean_up(self):
        try:
            logger.error("Cleaning up.")
            self.driver.quit()
        except Exception:
            logger.exception("Unable to clean up.", exc_info=True)


if __name__ == "__main__":
    try:
        cookie_clicker = CookieClicker()
        cookie_clicker.run()  
    except Exception:
        logger.exception("Program failed with exception...", exc_info=True)
        cookie_clicker.clean_up()
    finally:
        pass





