# coding: utf-8
import os
import re
import json
import warnings
from collections import OrderedDict
from abc import ABCMeta, abstractmethod
from kerasy.utils import toBLUE, toGREEN, toACCENT

from .utils._path import DOTENV_PATH
from .utils._warnings import (GummyImprementationWarning, 
                              JournalTypeIndistinguishableWarning)
from .utils.driver_utils import (try_find_element_click, click,
                                 try_find_element_send_keys, pass_forms)
from .utils.environ_utils import load_environ, TRANSLATION_GUMMY_ENVNAME_PREFIX
from .utils.generic_utils import mk_class_get
from .utils.journal_utils import whichJournal

class GummyAbstGateWay(metaclass=ABCMeta):
    """
    It is not possible to define all the patterns as the usage of gateway differs for each service and each journal. 
    Therefore, if you don't use `UTokyoGateWay`, define a new gateway class (please inherit this class with `passthrough` method).
    I would also appreciate if you could pull request about your own class.

    ```python
    # How to inherit `GummyAbstGateWay` class
    from gummy.gateways import GummyAbstGateWay
    class myGateWay(GummyAbstGateWay):
        def __init__(self, url, ...)
            super().__init__(url)
            :
    ```
    pass2journal()
    """
    def __init__(self, verbose=1, env_varnames=[], dotenv_path=DOTENV_PATH):
        self._setup(env_varnames=env_varnames)
        self.verbose = verbose
        load_environ(dotenv_path=dotenv_path, env_varnames=self.env_varnames)
    
    def _setup(self, env_varnames=[]):
        self.name  = self.__class__.__name__
        self.name_ = re.sub(r"([a-z])([A-Z])", r"\1_\2", self.name).lower()
        journal2method = {None : self._pass2others}
        for method in self.__dir__():
            match = re.match(pattern=r"_pass2(?!.*others)(.+)$", string=method)
            if match is not None:
                journal2method[match.group(1).lower()] = self.__getattribute__(match.group(0))
        self.journal2method = journal2method
        # Create necessary Environment Variables List.
        self.env_varnames = [
            TRANSLATION_GUMMY_ENVNAME_PREFIX + "_" + \
            self.__class__.__name__.replace('GateWay', '').upper() + "_" + \
            "GATEWAY_" + \
            v.upper() for v in env_varnames
        ]

    @property
    def supported_journals(self):
        return [journal for journal in self.journal2method.keys() if journal is not None]

    def show_supported_journals(self):
        for journal in self.supported_journals:
            print(f"- {journal}")

    def _pass2others(self, driver, **kwargs):
        """ 
        How to deal with urls of journals that 
        - do not require gateways.
        - have not been individually defined.
        In most cases you don't have to do anything (only return `drive`)
        """
        return_as_it_is = lambda cano_url, *args, **kwargs : cano_url
        return (driver, return_as_it_is)
        
    def passthrough(self, driver, url=None, journal_type=None, **gatewaykwargs):
        """
        @params driver        : (WebDriver) webdriver.
        @params url           : (str) URL you want to access using gateway.
        @params journal_type  : (str) journal type.
        @params gatewaykwargs : (dict) kwargs for `pass2journal`.
        @return driver        : (WebDriver) webdriver.
        @return fmt_url_func  : (function) convert canonicalized url to formatted url for gateway.
        """
        if len(self.supported_journals) == 0:
            msg = f"{toGREEN(self.name)} doesn't support any individual journal, please define " + \
                  f"a method corresponding to a journal named {toBLUE('Hoge')} with a name {toBLUE('_pass2hoge')}"
            warnings.warn(message=msg, category=GummyImprementationWarning)
        if journal_type is None:
            if url is None:
                msg = f"You don't specify both {toBLUE('url')} and {toBLUE('journal_type')}, so " + \
                      f"we could not distinguish the journal type."
                warnings.warn(message=msg, category=JournalTypeIndistinguishableWarning)                
            else:
                journal_type = whichJournal(url=url)
        pass2journal = self.journal2method.get(journal_type.lower(), self._pass2others)
        print(f"Use {toGREEN(self.name)} class and {toBLUE(pass2journal.__name__)} method.")
        driver, fmt_url_func = pass2journal(driver=driver, **gatewaykwargs)
        return (driver, fmt_url_func)

class UselessGateWay(GummyAbstGateWay):
    def __init__(self, verbose=1):
        super().__init__(
            verbose=verbose,
            env_varnames=[]
        )

class UTokyoGateWay(GummyAbstGateWay):
    def __init__(self, verbose=1):
        super().__init__(
            verbose=verbose,
            env_varnames=["username", "password"]
        )

    def _passthrough_base(self, driver, username=None, password=None):
        """ The underlying function to passthrough 
        # Example)
        def _pass2nature(self, driver, username=None, password=None, **kwargs):
            driver = self._passthrough_base(driver, username=username, password=password)
            :
        """
        kwargs = OrderedDict(**{
            "username"    : username or os.getenv("TRANSLATION_GUMMY_UTOKYO_GATEWAY_USERNAME"),
            "password"    : password or os.getenv("TRANSLATION_GUMMY_UTOKYO_GATEWAY_PASSWORD"),
            "btnSubmit_6" : click,
            "btnContinue" : click,
        })
        driver.get(url="https://gateway.itc.u-tokyo.ac.jp/dana-na/auth/url_default/welcome.cgi")
        driver = pass_forms(driver, **kwargs)
        driver.get(url="https://gateway.itc.u-tokyo.ac.jp/sslvpn1/,DanaInfo=www.dl.itc.u-tokyo.ac.jp,SSL+dbej.html")
        return driver

    def _pass2nature(self, driver, username=None, password=None, **gatewaykwargs):
        driver = self._passthrough_base(driver, username=username, password=password)
        driver.get("https://gateway.itc.u-tokyo.ac.jp/,DanaInfo=www.nature.com,SSL")
        current_url = driver.current_url
        def fmt_url_func(cano_url, *args, **kwargs):
            gateway_fmt_url = re.sub(
                pattern=r"^https?://www\.nature\.com\/(.*)$", 
                repl=fr"{current_url}\1", 
                string=cano_url
            )
            return gateway_fmt_url
        return driver, fmt_url_func

all = TranslationGummyGateWays = {
    "useless" : UselessGateWay,
    "utokyo"  : UTokyoGateWay,
}

get = mk_class_get(
    all_classes=TranslationGummyGateWays,
    gummy_abst_class=[GummyAbstGateWay],
    genre="gateways"
)