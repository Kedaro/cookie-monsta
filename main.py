from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import re



# TODO: find way to scan for bonuses
# TODO: implement other strategies

CHROME_DRIVER_PATH = "/home/syd/Desktop/utilities/chromedriver_linux64/chromedriver" 
SITE_URL = "https://orteil.dashnet.org/cookieclicker/"
UPGRADE_PATH = '//*[@id=\"upgrade0\"]'
COOKIE_COUNT_PATH = '//*[@id=\"cookies\"]'
COOKIE_PATH = '//*[@id=\"bigCookie\"]'
# estimated based on emprical evidence
CLICKS_PER_SECOND = 28

class CookieClicker(object):
    def __init__(self):
        self.driver = webdriver.Chrome(CHROME_DRIVER_PATH) 
        self.cookie = None
        self.product_num = 0
        self.loop_index = 1

    def run(self):
        self.driver.get(SITE_URL)
        # sleep to load
        time.sleep(2)
        self.cookie = self.driver.find_element_by_xpath(COOKIE_PATH)

        while True:

            for _ in range(CLICKS_PER_SECOND*2):
                self.cookie.click()
            
            self.purchase_upgrade_if_possible()

            purchase_product_num = self.product_num
            while purchase_product_num >= 0:
                # check if product is available
                product = self.driver.find_element_by_xpath(f"//*[@id=\"product{purchase_product_num}\"]")
                if product.get_attribute("class") == "product unlocked enabled":
                    # if available
                    print(f"Buying product {purchase_product_num}")
                    product.click()
                    if purchase_product_num == self.product_num:
                        self.product_num += 1
                        print(f"Incrementing product num to {self.product_num}")
                else:
                    purchase_product_num -= 1
                    continue
                break
            
    def purchase_upgrade_if_possible(self):
        try:
            upgrade = self.driver.find_element_by_xpath(UPGRADE_PATH)
            if upgrade.get_attribute("class") == "crate upgrade enabled":
                print("Buying upgrade")
                upgrade.click()
        except Exception as _:
            print("No upgrade available")

    def get_cookie_count(self) -> int:
        cookies = self.driver.find_element_by_xpath(COOKIE_COUNT_PATH)
        txt = cookies.text
        # remove from new line on
        txt_count = re.sub(r'\s.*$', "", txt)
        # remove cookies label
        txt_count = txt_count.strip(" cookies")
        # remove and commas
        txt_count = txt_count.strip(",")
        return int(txt_count)

    def clean_up(self):
        try:
            self.driver.quit()
        except Exception as e:
            print("Unable to clean up.")
            print(e)


if __name__ == "__main__":
    try:
        cookie_clicker = CookieClicker()
        cookie_clicker.run()  
    except Exception as e:
        print(e)
        cookie_clicker.clean_up()
    finally:
        pass





