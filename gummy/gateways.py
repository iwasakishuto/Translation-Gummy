# coding: utf-8
import os
import re
import json
import warnings
from collections import OrderedDict
from abc import ABCMeta, abstractmethod

from .utils._path import DOTENV_PATH
from .utils._warnings import GummyImprementationWarning
from .utils._exceptions import JournalTypeIndistinguishableError
from .utils.coloring_utils import toRED, toBLUE, toGREEN, toACCENT
from .utils.driver_utils import (try_find_element_click, click,
                                 try_find_element_send_keys, pass_forms)
from .utils.environ_utils import (load_environ, check_environ,
                                  TRANSLATION_GUMMY_ENVNAME_PREFIX)
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
    def __init__(self, verbose=True, required_kwargs={}, dotenv_path=DOTENV_PATH):
        self._setup(required_kwargs=required_kwargs)
        self.verbose = verbose
        load_environ(dotenv_path=dotenv_path, env_varnames=self.required_env_varnames.get("base"))
    
    def _setup(self, required_kwargs={}):
        self.name  = self.__class__.__name__
        self.name_ = re.sub(r"([a-z])([A-Z])", r"\1_\2", self.name).lower()

        # Create necessary Environment Variables List.
        if "base" not in required_kwargs:
            required_kwargs["base"] = []
        self.required_kwargs = {journal.lower():kwargs for (journal,kwargs) in required_kwargs.items()}

        # Setup Journal 2 method
        journal2method = {None : self._pass2others}
        for method in self.__dir__():
            # Find the method to pass through to each journal.
            match = re.match(pattern=r"_pass2(?!.*others)(.+)$", string=method)
            if match is not None:
                # match.group(0) : _pass2JOURNAL
                # match.group(1) : JOURNAL
                journal2method[match.group(1).lower()] = self.__getattribute__(match.group(0))
        self.journal2method = journal2method

    def toENV_VARNAMES(self, name):
        ENV_VARNAMES = "_".join([
            TRANSLATION_GUMMY_ENVNAME_PREFIX,
            re.sub(pattern=r"^(.*)GateWay$", repl=r"\1", string=self.name),
            "gateway",
            name,
        ]).upper()
        return ENV_VARNAMES

    @property
    def required_env_varnames(self):
        return {
            journal: [self.toENV_VARNAMES(kwarg) for kwarg in kwargs] 
            for (journal,kwargs) in self.required_kwargs.items()
        }

    @property
    def supported_journals(self):
        return [journal for journal in self.journal2method.keys() if journal is not None]

    def get_required_kwargs(self, journal_type=None):
        required_kwargs = self.required_kwargs.get("base")
        if journal_type is not None:
            required_kwargs += self.required_kwargs.get(journal_type.lower(), [])
        return list(set(required_kwargs))

    def get_required_env_varnames(self, journal_type=None):
        required_kwargs = self.get_required_kwargs(journal_type=journal_type)
        return [self.toENV_VARNAMES(kwarg) for kwarg in required_kwargs]

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
                raise JournalTypeIndistinguishableError(msg)                
            else:
                journal_type = whichJournal(url=url)
        journal_type = journal_type.lower()
        pass2journal = self.journal2method.get(journal_type, self._pass2others)
        if self.verbose: print(f"Use {toGREEN(self.name)}.{toBLUE(pass2journal.__name__)} method.")
        required_kwargs = self.get_required_kwargs(journal_type=journal_type)
        required_env_varnames = self.get_required_env_varnames(journal_type=journal_type)
        is_ok, _ = check_environ(required_kwargs=required_kwargs, required_env_varnames=required_env_varnames, verbose=self.verbose, **gatewaykwargs)
        if not is_ok:
            if self.verbose: print(f"[{toRED('instead')}] Use {toGREEN(self.name)} class and {toBLUE('pass2others')} method.")
            pass2journal = self._pass2others
        driver, fmt_url_func = pass2journal(driver=driver, **gatewaykwargs)
        return (driver, fmt_url_func)

class UselessGateWay(GummyAbstGateWay):
    def __init__(self, verbose=True):
        super().__init__(
            verbose=verbose,
            required_kwargs={}
        )

class UTokyoGateWay(GummyAbstGateWay):
    def __init__(self, verbose=True):
        super().__init__(
            verbose=verbose,
            required_kwargs={
                "base" : ["username", "password"]
            }
        )
        self._url = "https://www.u-tokyo.ac.jp/adm/dics/ja/gateway.html"

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

    def _pass2sciencedirect(self, driver, username=None, password=None, **gatewaykwargs):
        driver = self._passthrough_base(driver, username=username, password=password)
        driver.get("https://gateway.itc.u-tokyo.ac.jp/,DanaInfo=www.sciencedirect.com,SSO=U+")
        # https://gateway.itc.u-tokyo.ac.jp:11002
        current_url = driver.current_url
        def fmt_url_func(cano_url, *args, **kwargs):
            gateway_fmt_url = re.sub(
                pattern=r"^https?://www\.sciencedirect\.com\/(.*)$", 
                repl=fr"{current_url}\1", 
                string=cano_url
            )
            return gateway_fmt_url
        return driver, fmt_url_func

    def _pass2springer(self, driver, username=None, password=None, **gatewaykwargs):
        driver = self._passthrough_base(driver, username=username, password=password)
        driver.get("https://gateway.itc.u-tokyo.ac.jp/,DanaInfo=link.springer.com,SSO=U+")
        # https://gateway.itc.u-tokyo.ac.jp/,DanaInfo=link.springer.com,SSL+
        current_url = driver.current_url
        url, dana_info, ssl = current_url.split(",")
        def fmt_url_func(cano_url, *args, **kwargs):
            gateway_fmt_url = re.sub(
                pattern=r"^https?:\/\/link\.springer\.com\/(article\/.+)\/(.+)$", 
                repl=fr"{url}\1/,{dana_info},{ssl}\2", 
                string=cano_url
            )
            return gateway_fmt_url
        return driver, fmt_url_func
    
    def _pass2wiley(self, driver, username=None, password=None, **gatewaykwargs):
        driver = self._passthrough_base(driver, username=username, password=password)
        driver.get("https://gateway.itc.u-tokyo.ac.jp/,DanaInfo=onlinelibrary.wiley.com,SSL")
        # https://gateway.itc.u-tokyo.ac.jp:11050/
        current_url = driver.current_url
        def fmt_url_func(cano_url, *args, **kwargs):
            gateway_fmt_url = re.sub(
                pattern=r"^https?://onlinelibrary\.wiley\.com\/(.*)$", 
                repl=fr"{current_url}\1", 
                string=cano_url
            )
            return gateway_fmt_url
        return driver, fmt_url_func

    def _pass2ieee(self, driver, username=None, password=None, **gatewaykwargs):
        driver = self._passthrough_base(driver, username=username, password=password)
        driver.get("https://gateway.itc.u-tokyo.ac.jp/Xplore/home.jsp,DanaInfo=ieeexplore.ieee.org,SSL")
        # https://gateway.itc.u-tokyo.ac.jp:11028/Xplore/home.jsp
        current_url = driver.current_url.replace("Xplore/home.jsp", "")
        def fmt_url_func(cano_url, *args, **kwargs):
            gateway_fmt_url = re.sub(
                pattern=r"^https?://ieeexplore\.ieee\.org\/(.*)$", 
                repl=fr"{current_url}\1", 
                string=cano_url
            )
            return gateway_fmt_url
        return driver, fmt_url_func

    def _pass2oxfordacademic(self, driver, username=None, password=None, **gatewaykwargs):
        driver = self._passthrough_base(driver, username=username, password=password)
        driver.get("https://gateway.itc.u-tokyo.ac.jp/journals/,DanaInfo=academic.oup.com,SSL")
        # https://gateway.itc.u-tokyo.ac.jp:11020/journals/
        current_url = driver.current_url.replace("journals/", "")
        def fmt_url_func(cano_url, *args, **kwargs):
            gateway_fmt_url = re.sub(
                pattern=r"^https?://academic\.oup\.com\/(.*)$", 
                repl=fr"{current_url}\1", 
                string=cano_url
            )
            return gateway_fmt_url
        return driver, fmt_url_func

    def _pass2rsc(self, driver, username=None, password=None, **gatewaykwargs):
        driver = self._passthrough_base(driver, username=username, password=password)
        driver.get("https://gateway.itc.u-tokyo.ac.jp/en/,DanaInfo=pubs.rsc.org,SSL+journals?key=title&value=current")
        driver = try_find_element_click(driver=driver, identifier="action_46", by="id")
        # https://gateway.itc.u-tokyo.ac.jp/en/,DanaInfo=pubs.rsc.org,SSL+journals?key=title&value=current
        current_url = driver.current_url
        url, dana_info, _ = current_url.split(",")
        def fmt_url_func(cano_url, *args, **kwargs):
            gateway_fmt_url = re.sub(
                pattern=r"^https?:\/\/pubs\.rsc\.org\/en\/(content\/.+)\/(.+)$", 
                repl=fr"{url}\1/,{dana_info},SSL+\2", 
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