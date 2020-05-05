from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

PATH = "/home/syd/Desktop/utilities/chromedriver_linux64/chromedriver" 

try:
    driver = webdriver.Chrome(PATH)

    driver.get("https://orteil.dashnet.org/cookieclicker/")

    print(driver.title)


    time.sleep(3)

    cookie = driver.find_element_by_xpath('//*[@id=\"bigCookie\"]')

    product_num = 0
    for i in range(3):
        for j in range(50):
            cookie.click()
            time.sleep(0.1)

        product = driver.find_element_by_xpath(f"//*[@id=\"product{product_num}\"]")
        if not product.get_attribute("class") == "product locked disabled":
            print(f"Buying product {product_num}")
            product.click()
            product_num += 1


except Exception as e:
    print(e)
finally:
    driver.quit()





