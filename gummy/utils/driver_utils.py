# coding: utf-8
""" Utility programs for Selenium WebDriver. See `1. Installation — Selenium Python Bindings 2 documentation <https://selenium-python.readthedocs.io/installation.html#drivers>`_ for more details."""
import time
import warnings
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC

from ._warnings import DriverNotFoundWarning
from ._path import GUMMY_DIR
from .coloring_utils import toGRAY, toBLUE, toGREEN, toRED
from .generic_utils import get_latest_filename, try_wrapper, handleKeyError

SUPPORTED_DRIVER_TYPES = ["local", "remote"]

def _print_driver_check_log(is_succeed, driver_type):
    """Print logs."""
    if is_succeed:
        state = toGREEN("[success]")
        msg = "driver can be built."
    else:
        state = toRED("[failure]")
        msg = "driver can't be built."
    print(" ".join([state, driver_type, msg]))

def get_chrome_options(browser=False):
    """Get default chrome options.

    Args:
        browser (bool) : Whether you want to run Chrome with GUI browser. (default= ``False`` )

    Examples:
        >>> from gummy.utils import get_chrome_options
        >>> # browser == False (default)
        >>> op = get_chrome_options(browser=False)
        >>> op.arguments
        ['--no-sandbox',
        '--ignore-certificate-errors',
        '--disable-dev-shm-usage',
        '--headless']
        >>> op.experimental_options
        {}
        >>> # browser == True
        >>> op = get_chrome_options(browser=True)
        >>> op.arguments
        ['--no-sandbox',
        '--ignore-certificate-errors',
        '--disable-dev-shm-usage',
        '--kiosk-printing']
        >>> op.experimental_options
        {'prefs': {'profile.default_content_settings.popups': 1,
        'download.default_directory': '/Users/iwasakishuto/.gummy',
        'directory_upgrade': True}}
    """
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--disable-dev-shm-usage')
    if not browser:
        chrome_options.add_argument('--headless')
    else:
        chrome_options.add_experimental_option("prefs", {
            # "plugins.always_open_pdf_externally": True,
            "profile.default_content_settings.popups": 1,
            "download.default_directory": GUMMY_DIR,
            "directory_upgrade": True,
        })
        chrome_options.add_argument('--kiosk-printing')

    return chrome_options

def _check_driver(selenium_port="4444"):
    """Check the available drivers. (if one of the drivers is built, there is no problem)"""
    DRIVER_TYPE = ""
    chrome_options = get_chrome_options(browser=False)
    for driver_type in SUPPORTED_DRIVER_TYPES:
        try:
            with eval(f"_get_driver_{driver_type}(chrome_options, selenium_port=selenium_port)") as driver:
                DRIVER_TYPE = driver_type
                _print_driver_check_log(is_succeed=True, driver_type=driver_type)
        except Exception as e:
            _print_driver_check_log(is_succeed=False, driver_type=driver_type)
    return DRIVER_TYPE

def _get_driver_local(chrome_options, **kwargs):
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def _get_driver_remote(chrome_options, **kwargs):
    selenium_port = kwargs.get("selenium_port", "4444")
    driver = webdriver.Remote(
        command_executor=f'http://selenium:{selenium_port}/wd/hub',
        desired_capabilities=DesiredCapabilities.CHROME.copy(),
        options=chrome_options
    )
    return driver

############################
#  START: Check driver
############################

try:
    __DRIVER_SETUP__
except NameError:
    DRIVER_TYPE = _check_driver()
    print(f"DRIVER_TYPE: {toGREEN(DRIVER_TYPE)}")
    __DRIVER_SETUP__ = True
    if DRIVER_TYPE == "":
        warnings.warn(message="Fails to launch all supported drivers.", category=DriverNotFoundWarning)

############################
#  END: Check driver
############################

def get_driver(driver_type=DRIVER_TYPE, chrome_options=None, browser=False, selenium_port="4444"):
    """Get a driver that works in your current environment.

    Args:
        driver_type (str)              : driver type. (default= ``DRIVER_TYPE``)
        chrome_options (ChromeOptions) : Instance of ChromeOptions. If not specify, use :meth:`get_chrome_options() <gummy.utils.driver_utils.get_chrome_options>` to get default options. 
        browser (bool)                 : Whether you want to run Chrome with GUI browser. (default= ``False`` )
        selenium_port (str)            : selenium port number. This will be used when you run on `Docker <https://github.com/iwasakishuto/Translation-Gummy/tree/master/docker>`_
    """
    handleKeyError(lst=SUPPORTED_DRIVER_TYPES, driver_type=driver_type)
    if chrome_options is None: chrome_options = get_chrome_options(browser=browser)
    return eval(f"_get_driver_{driver_type}(chrome_options, selenium_port=selenium_port)")

def try_find_element(driver, by, identifier, timeout=3, verbose=True):
    """Find an element given a By strategy and locator.

    Wrap with :meth:`try_wrapper <gummy.utils.generic_utils.try_wrapper>` 
    to handle the error so that the programs does not stop in a series of processes.

    Args:
        driver (WebDriver) : Selenium WebDriver.
        by (str)           : Locator strategies. See `4. Locating Elements — Selenium Python Bindings 2 documentation <https://selenium-python.readthedocs.io/locating-elements.html>`_
        identifier (str)   : Identifier to find the element
        timeout (int)      : Number of seconds before timing out (default= ``3``)
        verbose (bool)     : Whether you want to print output or not. (default= ``True`` ) 

    Examples:
        >>> from gummy.utils import get_driver, try_find_element
        >>> with get_driver() as driver:
        ...     driver.get("https://www.google.com/")
        ...     e = try_find_element(driver=driver, by="tag name", identifier="img")
        Succeeded to locate element with tag name=img
    """
    return try_wrapper(
        func=WebDriverWait(driver=driver, timeout=timeout).until,
        msg_=f"locate element with {toGREEN(by)}={toBLUE(identifier)}",
        method=lambda x: x.find_element(by=by, value=identifier),
        verbose_=verbose,
    )

def try_find_element_send_keys(driver, by=None, identifier=None, values=(), target=None, timeout=3, verbose=True):
    """Find an element given a By strategy and locator, and Simulates typing into the element.

    Wrap with :meth:`try_wrapper <gummy.utils.generic_utils.try_wrapper>` 
    to handle the error so that the programs does not stop in a series of processes.

    Args:
        driver (WebDriver)  : Selenium WebDriver.
        by (str)            : Locator strategies. See `4. Locating Elements — Selenium Python Bindings 2 documentation <https://selenium-python.readthedocs.io/locating-elements.html>`_
        identifier (str)    : Identifier to find the element
        values (tuple)      : A string for typing, or setting form fields. For setting file inputs, this could be a local file path.
        target (WebElement) : Represents a DOM element. (If you already find element)
        timeout (int)       : Number of seconds before timing out (default= ``3``)
        verbose (bool)      : Whether you want to print output or not. (default= ``True`` ) 
    """
    if target is None:
        target = try_find_element(driver=driver, identifier=identifier, by=by, timeout=timeout)
    if target is not None:
        try_wrapper(
            target.send_keys,
            *tuple(values),
            msg_=f"fill {toBLUE(values)} in element with {toGREEN(by)}={toBLUE(identifier)}",
            verbose_=verbose,
        )
    
def try_find_element_click(driver, by=None, identifier=None, target=None, timeout=3, verbose=True):
    """Find an element given a By strategy and locator, and Clicks the element.

    Wrap with :meth:`try_wrapper <gummy.utils.generic_utils.try_wrapper>` 
    to handle the error so that the programs does not stop in a series of processes.

    Args:
        driver (WebDriver)  : Selenium WebDriver.
        by (str)            : Locator strategies. See `4. Locating Elements — Selenium Python Bindings 2 documentation <https://selenium-python.readthedocs.io/locating-elements.html>`_
        identifier (str)    : Identifier to find the element
        target (WebElement) : Represents a DOM element. (If you already find element)
        timeout (int)       : Number of seconds before timing out (default= ``3``)
        verbose (bool)      : Whether you want to print output or not. (default= ``True`` ) 
    """
    if target is None:
        target = try_find_element(driver=driver, identifier=identifier, by=by, timeout=timeout)
    if target is not None:
        def element_click(driver, target):
            try:
                driver.execute_script("arguments[0].click();", target)
            except StaleElementReferenceException:
                target.click()
        try_wrapper(
            func=element_click,
            msg_=f"click the element with {toGREEN(by)}={toBLUE(identifier)}",
            verbose_=verbose,
            driver=driver,
            target=target,
        )

def click():
    """ function for differentiation """

def pass_forms(driver, **kwargs):
    """Pass through forms.

    You can check the example in :meth:`passthrough_base <gummy.gateways.UTokyoGateWay.passthrough_base>`

    TODO:
        Currently, only ``"id"`` is supported as ``Locator strategies``. Need to 
        be selectable for generality

    Args:
        driver (WebDriver) : Selenium WebDriver.
        kwargs (dict)      : ``key`` is  ``identifier`` and ``val`` is
    """
    for k,v in kwargs.items():
        if callable(v) and v.__qualname__ == "click":
            try_find_element_click(driver=driver, by="id", identifier=k)
        else:
            try_find_element_send_keys(driver=driver, by="id", identifier=k, values=v)
    print(f"Current URL: {toBLUE(driver.current_url)}")

def download_PDF_with_driver(url, dirname=".", verbose=True, timeout=3):
    """Download PDF file with GUI driver.

    Args:
        url (str)       : File URL.
        dirname (str)   : The directory where downloaded data will be saved.
        verbose (bool)  : Whether print verbose or not.
        timeout (int)   : Number of seconds before timing out (default= ``3``)

    Returns:
        path (str) : path/to/downloaded_file
    """
    chrome_options = get_chrome_options(browser=True)
    if "prefs" not in chrome_options._experimental_options:
        chrome_options._experimental_options["prefs"] = {}
    chrome_options._experimental_options["prefs"]["download.default_directory"] = dirname
    chrome_options._experimental_options["prefs"]["plugins.always_open_pdf_externally"] = True
    if verbose: print(f"Downloading PDF from {toBLUE(url)}")
    with get_driver(chrome_options=chrome_options) as driver:
        driver.get(url)
        for _ in range(timeout):
            time.sleep(1)
            path = get_latest_filename(dirname=dirname)
            if not path.endswith(".crdownload"):
                break
    if verbose: print(f"Save PDF at {toBLUE(path)}")
    return path

def wait_until_all_elements(driver, timeout, verbose=True):
    """Wait until all elements visible.
    
    Args:
        driver (WebDriver) : Selenium WebDriver.
        timeout (int)      : Number of seconds before timing out (default= ``3``)
        verbose (bool)     : Whether you want to print output or not. (default= ``True`` ) 
    """
    if verbose: print(f"Wait up to {timeout}[s] for all page elements to load.")
    WebDriverWait(driver=driver, timeout=timeout).until(EC.presence_of_all_elements_located)
    time.sleep(timeout)

def scrollDown(driver, verbose=True):
    """Scroll down to the bottom of the page.
    
    Args:
        driver (WebDriver) : Selenium WebDriver.
        verbose (bool)     : Whether you want to print output or not. (default= ``True`` ) 
    """
    if verbose: print("Scroll down to the bottom of the page.")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")     
    # driver.find_element_by_tag_name('body').click()
    # driver.find_element_by_tag_name('body').send_keys(Keys.PAGE_DOWN)    
