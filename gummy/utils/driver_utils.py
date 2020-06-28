# coding: utf-8
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options

from kerasy.utils import toBLUE

chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-dev-shm-usage')

DRIVER_TYPE = "none"
try:
    driver = webdriver.Chrome(options=chrome_options)
    driver.quit()
    DRIVER_TYPE = "local"
except:
    pass

try:
    driver = webdriver.Remote(command_executor='http://selenium:4444/wd/hub',
                              desired_capabilities=DesiredCapabilities.CHROME.copy(),
                              options=chrome_options)
    driver.quit()
    DRIVER_TYPE = "remote"
except:
    pass


def get_driver():
    if DRIVER_TYPE=="remote":
        with webdriver.Remote(command_executor='http://selenium:4444/wd/hub',
                              desired_capabilities=DesiredCapabilities.CHROME.copy(),
                              options=chrome_options) as driver:
            return driver
    elif DRIVER_TYPE=="local":
        with webdriver.Chrome(options=chrome_options) as driver:
            return driver
    else:
        msg = "Could not create an instance of the 'chromedriver'. " + \
        "If you can not prepare 'chromedriver' executable locally, " + \
        "please build the environment with Dockerfile. Please see" + \
        toBLUE("https://github.com/iwasakishuto/Translation-Gummy/tree/master/docker")