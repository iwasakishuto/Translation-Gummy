# coding: utf-8
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options

from kerasy.utils import toBLUE, toGREEN, toRED

def print_log(is_succeed, pos):
    if is_succeed:
        flag = toGREEN("[success]")
        content = "driver can be built."
    else:
        flag = toRED("[failure]")
        content = "driver can't be built."
    print(" ".join([flag, pos, content]))

chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--ignore-certificate-errors')
# chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-dev-shm-usage')

DRIVER_TYPE = "none"
try:
    with webdriver.Chrome(options=chrome_options) as driver:
        DRIVER_TYPE = "local"
        print_log(is_succeed=True, pos="local")
except:
    print_log(is_succeed=False, pos="local")

try:
    with webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        desired_capabilities=DesiredCapabilities.CHROME.copy(),
        options=chrome_options) as driver:
        DRIVER_TYPE = "remote"
        print_log(is_succeed=True, pos="remote")
except:
    print_log(is_succeed=False, pos="remote")
print(f"DRIVER_TYPE: {toGREEN(DRIVER_TYPE)}")

def get_driver():
    if DRIVER_TYPE=="remote":
        driver = webdriver.Remote(command_executor='http://selenium:4444/wd/hub',
                                  desired_capabilities=DesiredCapabilities.CHROME.copy(),
                                  options=chrome_options)
        return driver
    elif DRIVER_TYPE=="local":
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    else:
        msg = "Could not create an instance of the 'chromedriver'. " + \
        "If you can not prepare 'chromedriver' executable locally, " + \
        "please build the environment with Dockerfile. Please see" + \
        toBLUE("https://github.com/iwasakishuto/Translation-Gummy/tree/master/docker")