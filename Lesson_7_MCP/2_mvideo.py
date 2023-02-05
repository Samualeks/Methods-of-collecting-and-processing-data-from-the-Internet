import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient

client = MongoClient('127.0.0.1', 27017)
db = client['base_mvideo']
trends_db = db.mvideo_trends

chrome_options = Options()
chrome_options.add_argument("--windows-size=1920,1080")
# chrome_options.add_argument("--start-maximized")
driver = webdriver.Chrome(executable_path='chromedriver.exe', options=chrome_options)
driver.implicitly_wait(15)

url = 'https://www.mvideo.ru'
driver.get(url)
driver.execute_script("window.scrollTo(0, window.scrollY + 1600)")


buttons = driver.find_elements(By.CLASS_NAME, 'tab-button')

button_trend = buttons[1]
button_trend.click()
trends = driver.find_element(By.XPATH, "//mvid-shelf-group[@class='page-carousel-padding ng-star-inserted']")



while True:
    try:
        # wait = WebDriverWait(driver, 15)
        button_next = trends.find_element(By.XPATH, "//mvid-carousel[@class='carusel ng-star-inserted']//"
                                                "button[@class='btn forward mv-icon-button--primary mv-icon-button--shadow mv-icon-button--medium mv-button mv-icon-button']")
        # button_next = wait.until(EC.element_to_be_clickable((By.XPATH, "//mvid-carousel[@class='carusel ng-star-inserted']//"
        #                                                                                   "button[@class='btn forward mv-icon-button--primary mv-icon-button--shadow mv-icon-button--medium mv-button mv-icon-button']")))

        button_next.click()

    except:
        break


goods = buttons[0].find_elements(By.XPATH, "./ancestor::mvid-shelf-group")
# goods = trends.find_elements(By.XPATH, "./ancestor::mvid-shelf-group")
# goods = trends.find_elements(By.XPATH, "//mvid-shelf-group[@class='page-carousel-padding ng-star-inserted']"
#                                        "//div[contains(@class,'ng-star-inserted')]")

names = goods[0].find_elements(By.XPATH, "//div[@class='title']")
links = goods[0].find_elements(By.XPATH, "//div[@class='title']/a[@href]")
rating_list = goods[0].find_elements(By.XPATH, "//div[@class='product-mini-card__rating ng-star-inserted']//"
                                         "span[@class='value ng-star-inserted']")

prices = goods[0].find_elements(By.XPATH, "//div[@class='product-mini-card__price ng-star-inserted']//"
                                          "span[@class='price__main-value']")

item = {}
for name, rating, link, price in zip(names, rating_list, links, prices):


    item['name'] = name.text
    item['rating'] = rating.text
    item['link'] = link.get_attribute("href")
    item['price'] = price.text

    trends_db.update_one({'link': item['link']}, {'$set': item}, upsert=True)


driver.quit()


if __name__ == '__main__':
    sys.exit(_main())