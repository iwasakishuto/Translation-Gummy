# coding: utf-8
"""If you want to use your gateway (not listed here), please inherit ``GummyAbstGateWay`` class and create your own class. 
I would also appreciate if you could do `"pull request" <https://github.com/iwasakishuto/Translation-Gummy/pulls>`_ about your own class :) 

The following information may be useful when you create your own class

.. csv-table::
   :header: content, position
   :widths: 15, 5

   "What is :meth:`passthrough_base <gummy.gateways.GummyAbstGateWay.passthrough_base>` and ``_pass2{journal_name}``", ":meth:`setup <gummy.gateways.GummyAbstGateWay.keyname2envname>` method"
   "How to set a environment variables, or give a kwargs", ":meth:`passthrough <gummy.gateways.GummyAbstGateWay.passthrough>` method"

You can easily get (import) ``Gateway Class`` by the following ways.

.. code-block:: python

    >>> from gummy import gateways
    >>> gateway = gateways.get("useless")
    <gummy.gateways.UselessGateWay at 0x124a4de50>
    >>> from gummy.gateways import UselessGateWay
    >>> useless = UselessGateWay()
    >>> gateway = gateways.get(useless)
    >>> gateway
    <gummy.gateways.UselessGateWay at 0x124a08730>
    >>> id(gateway) == id(useless)
    True
"""
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
from .utils.driver_utils import try_find_element_click, click, try_find_element_send_keys, pass_forms
from .utils.environ_utils import load_environ, check_environ, name2envname
from .utils.generic_utils import mk_class_get
from .utils.journal_utils import whichJournal

class GummyAbstGateWay(metaclass=ABCMeta):
    """If you want to create your own gateway class, please inherit this class.

    Args:
        verbose (bool)           : Whether to print message or not. (default= ``True``)
        required_keynames (dict) : Required keynames for :meth:`passthrough_base <gummy.gateways.GummyAbstGateWay.passthrough_base>` or ``_pass2{journal_name}`` method. See :meth:`setup <gummy.gateways.GummyAbstGateWay.keyname2envname>`.
        dotenv_path (str)        : where the dotenv file is. (default is ``where_is_envfile()``)

    Attributes:
        required_keynames (dict) : Required ``kwargs``. ( ``journal_name`` -> ``key_list`` )
        journal2method (dict)    : Which method to use. Use :meth:`_pass2others <gummy.gateways.GummyAbstGateWay._pass2others>` for journal which does not exist in the key. ( ``journal_name`` -> ``method`` ) 
    """
    def __init__(self, verbose=True, required_keynames={}, dotenv_path=DOTENV_PATH):
        self.setup(required_keynames=required_keynames)
        self.verbose = verbose
        load_environ(
            dotenv_path=dotenv_path, 
            env_varnames=self.required_env_varnames.get("base"), 
            verbose=verbose,
        )

    @property
    def class_name(self):
        """Same as ``self.__class__.__name__``."""
        return self.__class__.__name__

    @property
    def name(self):
        """Gateway service name. It is used for converting key name to environment varname. see :meth:`keyname2envname <gummy.gateways.GummyAbstGateWay.keyname2envname>` method."""
        return self.class_name.replace("GateWay", "")

    def setup(self, required_keynames={}):
        """Setup

        If you want to use your gateway service, you will probably need to 
        
        1. log in with your ``username`` and ``password`` to use the gateway service
        2. process for each service. (it is expected that the required information or required process will differ for each journal)
        
        To make it easier to add a supported journals, ``1`` will be handled by 
        :meth:`passthrough_base <gummy.gateways.GummyAbstGateWay.passthrough_base>` method, and ``2`` will be handled by ``_pass2{journal_name}`` 
        method, so when adding a supported journal, only ``_pass2{journal_name}`` needs to be added.

        If there is any information you have to fill in when using gateway service, you need to give ``required_keynames``.
        
        .. code-block:: python

            >>> class UTokyoGateWay(GummyAbstGateWay):
            ...     def __init__(self):
            ...         super().__init__(
            ...             required_keynames={
            ...                 "base" : ["username", "password"]
            ...             }
            ...         )

        - ``"base"`` is the key for :meth:`passthrough_base <gummy.gateways.GummyAbstGateWay.passthrough_base>` method.
        - ``"{journal_name}"`` is the key for ``_pass2{journal_name}`` method.

        Args:
            required_keynames (dict) : Required ``kwargs`` for ``passthrough`` method.
        """
        # Create necessary Environment Variables List.
        if "base" not in required_keynames:
            required_keynames["base"] = []
        self.required_keynames = {journal.lower():kwargs for (journal,kwargs) in required_keynames.items()}

        # Setup Journal 2 method
        journal2method = {None : self._pass2others}
        for method_name in dir(self):
            # Find the method to pass through to each journal.
            match = re.match(pattern=r"_pass2(?!.*others)(.+)$", string=method_name)
            if match is not None:
                journal_name = match.group(1).lower()
                journal2method[journal_name] = getattr(self, method_name)
        self.journal2method = journal2method
    
    def keyname2envname(self, keyname):
        """Convert keyname to environment varname.

        Args
            keyname (str) : Keyname for :meth:`passthrough_base <gummy.gateways.GummyAbstGateWay.passthrough_base>` or ``_pass2{journal_name}`` method.

        Examples:
            >>> from gummy.gateways import UselessGateWay
            >>> gateway = UselessGateWay()
            >>> gateway.keyname2envname("name")
            'TRANSLATION_GUMMY_GATEWAY_USELESS_NAME'
            >>> gateway.keyname2envname("hoge")
            'TRANSLATION_GUMMY_GATEWAY_USELESS_HOGE'
        """
        return name2envname(name=keyname, prefix=self.name, service="gateway")

    @property
    def required_env_varnames(self):
        """Required environment varnames.

        Examples:
            >>> from gummy.gateways import UTokyoGateWay
            >>> gateway = UTokyoGateWay()
            >>> gateway.required_env_varname
            {'base': ['TRANSLATION_GUMMY_GATEWAY_UTOKYO_USERNAME',
            'TRANSLATION_GUMMY_GATEWAY_UTOKYO_PASSWORD']}
        """
        return {
            journal: [self.keyname2envname(keyname) for keyname in keynames] 
            for (journal,keynames) in self.required_keynames.items()
        }

    @property
    def supported_journals(self):
        """Supported journals. Use :meth:`_pass2others <gummy.gateways.GummyAbstGateWay._pass2others>` method for other journals.

        Examples:
            >>> from gummy.gateways import UTokyoGateWay
            >>> gateway = UTokyoGateWay()
            >>> gateway.supported_journals
            ['ieee',
                :
            'wileyonlinelibrary']
        """
        return [journal for journal in self.journal2method.keys() if journal is not None]

    def get_required_keynames(self, journal_type=None):
        """Get required keynames for given ``journal_type``.

        Args:
            journal_type (str) : Journal name.

        Examples:
            >>> from gummy.gateways import UTokyoGateWay
            >>> gateway = UTokyoGateWay()
            >>> gateway.get_required_keynames("ieee")
            ['password', 'username']
        """
        required_keynames = self.required_keynames.get("base")
        if journal_type is not None:
            required_keynames += self.required_keynames.get(journal_type.lower(), [])
        return list(set(required_keynames))

    def get_required_env_varnames(self, journal_type=None):
        """Get required keynames for given ``journal_type``.

        Args:
            journal_type (str) : Journal name.

        Examples:
            >>> from gummy.gateways import UTokyoGateWay
            >>> gateway = UTokyoGateWay()
            >>> gateway.get_required_env_varnames("ieee")
            ['TRANSLATION_GUMMY_GATEWAY_UTOKYO_PASSWORD',
            'TRANSLATION_GUMMY_GATEWAY_UTOKYO_USERNAME']
        """
        required_keynames = self.get_required_keynames(journal_type=journal_type)
        return [self.keyname2envname(kwarg) for kwarg in required_keynames]

    def get_val(self, keyname, **gatewaykwargs):
        """Get the value from ``gatewaykwargs`` or an environment variable.

        Args:
            keyname (str)        : Keyname for :meth:`passthrough_base <gummy.gateways.GummyAbstGateWay.passthrough_base>` or ``_pass2{journal_name}`` method.
            gatewaykwargs (dict) : Given ``gatewaykwargs``.

        Examples:
            >>> from gummy.gateways import UTokyoGateWay
            >>> gateway = UTokyoGateWay()
            >>> print(gateway.get_val("hoge"))
            None
            >>> print(gateway.get_val("username"))
            USERNAME_IN_ENVFILE
            >>> print(gateway.get_val("username", username=":)"))
            :)
        """
        return gatewaykwargs.get(keyname) or os.getenv(self.keyname2envname(keyname))

    @abstractmethod
    def passthrough_base(driver, **gatewaykwargs):
        """Perform necessary processing when using gateway service regardless of journal.
        
        Args:
            driver (WebDriver)   : Selenium WebDriver.
            gatewaykwargs (dict) : Given ``gatewaykwargs``.
        """
        return driver

    def _pass2others(self, driver, **kwargs):
        """Perform the necessary procedures to access journals whose method 
        (``_pass2{journal_name}``) is not defined individually. In most cases 
        you don't have to do anything (only return driver as it is.)

        Args:
            driver (WebDriver) : Selenium WebDriver.

        Return:
            tuple (WebDriver, function): (Selenium WebDriver, How to convert raw URL to sslURL)
        """
        return_as_it_is = lambda cano_url, *args, **kwargs : cano_url
        return (driver, return_as_it_is)

    def passthrough(self, driver, url=None, journal_type=None, **gatewaykwargs):
        """Perform the necessary procedures to access journals and return WebDriver 
        and function which converts raw URL to ssl URL. When you use gateway service, 
        you need to **set environment variables in .env file**, or call a method 
        with keyword argment.

        * **Set environment variables in .env file. (recommended):**

            .. code-block:: python

                >>> # Write and update `.env` file.
                >>> from gummy.utils import show_environ, write_environ, read_environ
                >>> write_environ(
                ...    TRANSLATION_GUMMY_GATEWAY_UTOKYO_USERNAME="username",
                ...    TRANSLATION_GUMMY_GATEWAY_UTOKYO_PASSWORD="password",
                >>> )
                >>> show_environ(default_dotenv_path)
                * TRANSLATION_GUMMY_GATEWAY_UTOKYO_USERNAME : "username"
                * TRANSLATION_GUMMY_GATEWAY_UTOKYO_PASSWORD : "password"
                >>> # Call with no kwargs.
                >>> from gummy.utils import get_driver
                >>> from gummy import gateways
                >>> gateway = gateways.get("utokyo")
                >>> with get_drive() as driver:
                ...    driver = gateway.passthrough(driver)
                ...    :

        * Call a function with keyword argument:

            .. code-block:: python

                >>> from gummy.utils import get_driver
                >>> from gummy import gateways
                >>> gateway = gateways.get("utokyo")
                >>> with get_drive() as driver:
                ...    driver = gateway.passthrough(driver, username="username", password="password")
                ...    :

        Args:
            driver (WebDriver)   : Selenium WebDriver.
            url (str)            : URL you want to access using gateway.
            journal_type (str)   : journal type. Give if known in advance. (default= ``None``)
            gatewaykwargs (dict) : kwargs for ``_pass2{journal}``

        Return:
            tuple (WebDriver, function): (Selenium WebDriver, How to convert raw URL to sslURL)
        """
        # Distinguish journal type and normalize (lower)
        if journal_type is None:
            if url is None:
                msg = f"You don't specify both {toBLUE('url')} and {toBLUE('journal_type')}, so {toGREEN(self.class_name)} could not distinguish the journal type."
                raise JournalTypeIndistinguishableError(msg=msg)            
            else:
                journal_type = whichJournal(url=url, driver=driver)
        journal_type = journal_type.lower()
        # Get the method to use to access the journal.
        pass2journal = self.journal2method.get(journal_type, self._pass2others)
        if self.verbose: print(f"Use {toGREEN(self.class_name)}.{toBLUE(pass2journal.__name__)} method.")
        # Check if the gateway serive (for given journal) is available with environment varnames and given ``kwargs``.
        required_keynames = self.get_required_keynames(journal_type=journal_type)
        required_env_varnames = self.get_required_env_varnames(journal_type=journal_type)
        is_ok, _ = check_environ(required_keynames=required_keynames, required_env_varnames=required_env_varnames, verbose=self.verbose, **gatewaykwargs)
        if not is_ok:
            if self.verbose: print(f"[{toRED('instead')}] Use {toBLUE('_pass2others')} method.")
            pass2journal = self._pass2others
        # Use gateway service with method.
        driver = self.passthrough_base(driver, **gatewaykwargs)
        driver, fmt_url_func = pass2journal(driver=driver, **gatewaykwargs)
        return (driver, fmt_url_func)

class UselessGateWay(GummyAbstGateWay):
    """Use this class when you do not use the gateway service."""
    def __init__(self, verbose=True):
        super().__init__(
            verbose=verbose,
            required_keynames={}
        )

    def passthrough_base(self, driver, **gatewaykwargs):
        """Do nothing."""
        return driver

class UTokyoGateWay(GummyAbstGateWay):
    """Authentication Gateway Service for students at `the University of Tokyo <https://www.u-tokyo.ac.jp/en/index.html>`_.

    This class is not available except for students. 
    `Authentication Gateway Service <https://www.u-tokyo.ac.jp/adm/dics/ja/gateway.html>`_ 
    is for faculty and staff members.

    .. code-block:: python

        >>> from gummy import gateways
        >>> gateway = gateways.get("utokyo")
        >>> gateway.required_env_varnames
        {'base': ['TRANSLATION_GUMMY_GATEWAY_UTOKYO_USERNAME',
        'TRANSLATION_GUMMY_GATEWAY_UTOKYO_PASSWORD']}
        >>> gateway.required_keynames
        {'base': ['username', 'password']}
    """
    def __init__(self, verbose=True):
        super().__init__(
            verbose=verbose,
            required_keynames={
                "base" : ["username", "password"]
            }
        )
        self._url = "https://www.u-tokyo.ac.jp/adm/dics/ja/gateway.html"

    def passthrough_base(self, driver, **gatewaykwargs):
        """Access `SSL-VPN Gateway of Information Technology Center, The University of Tokyo <https://gateway.itc.u-tokyo.ac.jp/dana-na/auth/url_default/welcome.cgi>`_ and do the necessary processing."""
        kwargs = OrderedDict(**{
            "username"    : self.get_val("username", **gatewaykwargs),
            "password"    : self.get_val("password", **gatewaykwargs),
            "btnSubmit_6" : click,
            "btnContinue" : click,
        })
        driver.get(url="https://gateway.itc.u-tokyo.ac.jp/dana-na/auth/url_default/welcome.cgi")
        pass_forms(driver=driver, **kwargs)
        driver.get(url="https://gateway.itc.u-tokyo.ac.jp/sslvpn1/,DanaInfo=www.dl.itc.u-tokyo.ac.jp,SSL+dbej.html")
        return driver

    def _pass2nature(self, driver, **gatewaykwargs):
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

    def _pass2sciencedirect(self, driver, **gatewaykwargs):
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

    def _pass2springer(self, driver, **gatewaykwargs):
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
    
    def _pass2wileyonlinelibrary(self, driver, **gatewaykwargs):
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

    def _pass2ieeexplore(self, driver, **gatewaykwargs):
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

    def _pass2oxfordacademic(self, driver, **gatewaykwargs):
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

    def _pass2rsc(self, driver, **gatewaykwargs):
        driver.get("https://gateway.itc.u-tokyo.ac.jp/en/,DanaInfo=pubs.rsc.org,SSL+journals?key=title&value=current")
        try_find_element_click(driver=driver, identifier="action_46", by="id")
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

    def _pass2nejm(self, driver, **gatewaykwargs):
        driver.get("https://gateway.itc.u-tokyo.ac.jp/,DanaInfo=www.nejm.org,SSL")
        # https://gateway.itc.u-tokyo.ac.jp/,DanaInfo=www.nejm.org,SSL
        current_url = driver.current_url
        url, dana_info, _ = current_url.split(",")
        def fmt_url_func(cano_url, *args, **kwargs):
            gateway_fmt_url = re.sub(
                pattern=r"^https?:\/\/www\.nejm\.org\/(doi\/.+)\/(.+)$", 
                repl=fr"{url}\1/,{dana_info},SSL+\2", 
                string=cano_url
            )
            return gateway_fmt_url
        return driver, fmt_url_func

    def _pass2pnas(self, driver, **gatewaykwargs):
        driver.get("https://gateway.itc.u-tokyo.ac.jp/,DanaInfo=www.pnas.org,SSO=U+")
        # https://gateway.itc.u-tokyo.ac.jp/,DanaInfo=www.pnas.org,SSL+
        current_url = driver.current_url
        url, dana_info, _ = current_url.split(",")
        def fmt_url_func(cano_url, *args, **kwargs):
            gateway_fmt_url = re.sub(
                pattern=r"^https?://www\.pnas\.org\/(content\/.+)\/(.+)$",                 
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
    genre="gateways",
)