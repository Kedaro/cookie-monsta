from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from count_cookies import cookie_count_text_to_float
from config import INITIAL_CPS_BUILDINGS
import time
import re
import logging


# TODO: cps of building needs to be updated as upgrades are bought
# TODO: only update buiding cps table if upgrade or building was bought
# TODO: add discount for future value of cookies? how long need to save before cna buy building.
# TODO: configurable strategy (greedy, discount future)

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

class CookieClicker(object):
    def __init__(self):
        self.driver = webdriver.Chrome(CHROME_DRIVER_PATH) 
        self.cookie = None
        self.upgrade = None

        self.cost_per_cps = dict()

        self.product_num = 0
        self.loop_index = 1

    def run(self):
        self.driver.get(SITE_URL)
        # sleep to load
        time.sleep(2)
        self.cookie = self.driver.find_element_by_xpath(COOKIE_PATH)

        while True:

            start = time.time()
            for _ in range(CLICKS_PER_SECOND*2):
                self.cookie.click()
            
            self.click_golden_cookie_if_possible()
            self.purchase_upgrade_if_possible()

            #self.get_cps_product()

            purchase_product_num = 0
            while purchase_product_num <= MAX_BUILING_INDEX: 
                # check if product is unlocked
                product = self.driver.find_element_by_xpath(f"//*[@id=\"product{purchase_product_num}\"]")            
                if product.get_attribute("class") in ("product unlocked enabled", "product unlocked disabled"):
                    self.cost_per_cps[purchase_product_num] = self.get_weighted_price_building(purchase_product_num)
                    purchase_product_num += 1
                    continue
                # if still locked, ignore it and the rest (because unlocked sequentially)
                break

            # most efficient building key
            best_building = min(self.cost_per_cps, key=self.cost_per_cps.get)
            # check if available
            product = self.driver.find_element_by_xpath(f"//*[@id=\"product{best_building}\"]")
            if product.get_attribute("class") == "product unlocked enabled":
                product.click()
                logger.debug(f"Buying product {best_building}")
            # otherwise wait to buy
            else:
                logger.debug(f"Waiting to buy product {best_building}")
                pass
            
            logger.debug(f"Loop time {time.time() - start}")
            
    def get_cps_product(self):
        action = ActionChains(self.driver)

        parent_level_menu = self.driver.find_element_by_xpath(f"//*[@id=\"product0\"]") 
        action.move_to_element(parent_level_menu).perform()

        tooltip = self.driver.find_element_by_xpath(f"//*[@id=\"tooltip\"]")
    
    def click_golden_cookie_if_possible(self):
            try:
                golden_cookies_children = self.driver.find_element_by_xpath("//*[@id=\"goldenCookie\"]").find_elements_by_xpath(".//*")
                shimmers_children = self.driver.find_element_by_xpath("//*[@id=\"shimmers\"]").find_elements_by_xpath(".//*")
                
                # TODO: add seasons popup

                # check if populated
                if len(golden_cookies_children) > 0:
                    child = golden_cookies_children[0]
                    logger.info("About to click golden cookie child")
                    child.click()
                    logger.info("Clicked golden cookie")
                if len(shimmers_children) > 0:
                    child = shimmers_children[0]
                    logger.info("About to click  shimers child child")
                    child.click()
                    logger.info("Clicked shimers child")
            except:
                logger.error("Failed to click bonus")
    
    def get_weighted_price_building(self, building_num: int):
        price_obj = self.driver.find_element_by_xpath(f"//*[@id=\"productPrice{building_num}\"]")
        cost_per_cps = cookie_count_text_to_float(price_obj.text)/INITIAL_CPS_BUILDINGS[building_num]
        #logger.debug(f"Building {building_num} has cost/cps {cost_per_cps}")
        return cost_per_cps
    
    def purchase_upgrade_if_possible(self):
        try:
            # define only if not defined
            if self.upgrade is None:
                self.upgrade = self.driver.find_element_by_xpath(UPGRADE_PATH)
            #try to click if you can
            if self.upgrade.get_attribute("class") == "crate upgrade enabled":
                logger.debug("Buying upgrade")
                self.upgrade.click()
                self.upgrade = None
        except Exception as _:
            self.upgrade = None
            logger.debug("No upgrade available")


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





