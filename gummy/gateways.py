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
import urllib
from abc import ABCMeta, abstractmethod
from typing import Any, Dict, List, Optional

from selenium.webdriver.remote.webdriver import WebDriver

from .utils._exceptions import JournalTypeIndistinguishableError
from .utils._path import DOTENV_PATH
from .utils._type import T_FORM_ACTION, T_PASSTHROGU_JOURNAL
from .utils.coloring_utils import toBLUE, toGREEN, toRED
from .utils.driver_utils import click, pass_forms, try_find_element_click
from .utils.environ_utils import check_environ, load_environ, name2envname
from .utils.generic_utils import mk_class_get, verbose2print
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

    def __init__(self, verbose: bool = True, required_keynames: Dict[str, str] = {}, dotenv_path: str = DOTENV_PATH):
        self.setup(required_keynames=required_keynames)
        self.verbose = verbose
        self.print = verbose2print(verbose=verbose)
        load_environ(
            dotenv_path=dotenv_path,
            env_varnames=self.required_env_varnames.get("base"),
            verbose=verbose,
        )

    @property
    def class_name(self) -> str:
        """Same as ``self.__class__.__name__``."""
        return self.__class__.__name__

    @property
    def name(self) -> str:
        """Gateway service name. It is used for converting key name to environment varname. see :meth:`keyname2envname <gummy.gateways.GummyAbstGateWay.keyname2envname>` method."""
        return self.class_name.replace("GateWay", "")

    def setup(self, required_keynames: Dict[str, str] = {}) -> None:
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
        self.required_keynames = {journal.lower(): kwargs for (journal, kwargs) in required_keynames.items()}

        # Setup Journal 2 method
        journal2method = {None: self._pass2others}
        for method_name in dir(self):
            # Find the method to pass through to each journal.
            match = re.match(pattern=r"_pass2(?!.*others)(.+)$", string=method_name)
            if match is not None:
                journal_name = match.group(1).lower()
                journal2method[journal_name] = getattr(self, method_name)
        self.journal2method = journal2method

    def keyname2envname(self, keyname: str) -> str:
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
    def required_env_varnames(self) -> Dict[str, List[str]]:
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
            for (journal, keynames) in self.required_keynames.items()
        }

    @property
    def supported_journals(self) -> List[str]:
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

    def get_required_keynames(self, journal_type: Optional[str] = None) -> List[str]:
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

    def get_required_env_varnames(self, journal_type: Optional[str] = None) -> List[str]:
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

    def get_val(self, keyname: str, **gatewaykwargs) -> Any:
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
    def passthrough_base(self, driver: WebDriver, **gatewaykwargs) -> WebDriver:
        """Perform necessary processing when using gateway service regardless of journal.

        Args:
            driver (WebDriver)   : Selenium WebDriver.
            gatewaykwargs (dict) : Given ``gatewaykwargs``.
        """
        return driver

    def _pass2others(self, driver: WebDriver, **kwargs) -> T_PASSTHROGU_JOURNAL:
        """Perform the necessary procedures to access journals whose method
        (``_pass2{journal_name}``) is not defined individually. In most cases
        you don't have to do anything (only return driver as it is.)

        Args:
            driver (WebDriver) : Selenium WebDriver.

        Return:
            tuple (WebDriver, function): (Selenium WebDriver, How to convert raw URL to sslURL)
        """
        return_as_it_is = lambda cano_url, *args, **kwargs: cano_url
        return (driver, return_as_it_is)

    def passthrough(
        self, driver: WebDriver, url: Optional[str] = None, journal_type: Optional[str] = None, **gatewaykwargs
    ) -> T_PASSTHROGU_JOURNAL:
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
        self.print(f"Gateway Method: {toGREEN(self.class_name)}.{toBLUE(pass2journal.__name__)}")
        # Check if the gateway serive (for given journal) is available with environment varnames and given ``kwargs``.
        required_keynames = self.get_required_keynames(journal_type=journal_type)
        required_env_varnames = self.get_required_env_varnames(journal_type=journal_type)
        is_ok, _ = check_environ(
            required_keynames=required_keynames,
            required_env_varnames=required_env_varnames,
            verbose=self.verbose,
            **gatewaykwargs,
        )
        if not is_ok:
            self.print(f"[{toRED('instead')}] Use {toBLUE('_pass2others')} method.")
            pass2journal = self._pass2others
        # Use gateway service with method.
        driver = self.passthrough_base(driver, **gatewaykwargs)
        driver, fmt_url_func = pass2journal(driver=driver, **gatewaykwargs)
        return (driver, fmt_url_func)


class UselessGateWay(GummyAbstGateWay):
    """Use this class when you do not use the gateway service."""

    def __init__(self, verbose: bool = True):
        super().__init__(verbose=verbose, required_keynames={})

    def passthrough_base(self, driver: WebDriver, **gatewaykwargs) -> WebDriver:
        """Do nothing."""
        return driver


class UTokyoGateWay(GummyAbstGateWay):
    """Authentication Gateway Service for students at `the University of Tokyo <https://www.u-tokyo.ac.jp/en/index.html>`_.

    This class is not available except for students.
    `E-journal & E-book Portal | 東京大学附属図書館 <https://www.lib.u-tokyo.ac.jp/ja/library/contents/database/1>`_
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

    def __init__(self, verbose: bool = True):
        super().__init__(verbose=verbose, required_keynames={"base": ["username", "password"]})
        # self._url = "https://www.u-tokyo.ac.jp/adm/dics/ja/gateway.html"
        self._url = "https://www.lib.m.u-tokyo.ac.jp/journals/remote.html"

    def passthrough_base(self, driver: WebDriver, _hide_value: bool = True, **gatewaykwargs) -> WebDriver:
        """Access `E-journal & E-book Portal | 東京大学附属図書館 <https://www.lib.u-tokyo.ac.jp/ja/library/contents/database/1>`_ and do the necessary processing."""
        formData: List[T_FORM_ACTION] = [
            dict(
                action="send_keys",
                by="id",
                identifier="userNameInput",
                values=self.get_val("username", **gatewaykwargs),
            ),
            dict(
                action="send_keys",
                by="id",
                identifier="passwordInput",
                values=self.get_val("password", **gatewaykwargs),
            ),
            dict(action=click, by="id", identifier="submitButton"),
        ]
        driver.get(url="https://utokyo.idm.oclc.org/login")
        pass_forms(driver=driver, formData=formData, _hide_value=_hide_value)
        # driver.get(url="https://gateway.itc.u-tokyo.ac.jp/sslvpn1/,DanaInfo=www.dl.itc.u-tokyo.ac.jp,SSL+dbej.html")
        return driver

    def _pass2nature(self, driver: WebDriver, **gatewaykwargs) -> T_PASSTHROGU_JOURNAL:
        def fmt_url_func(cano_url: str, *args, **kwargs) -> str:
            return urllib.parse.urljoin(
                base="https://www-nature-com.utokyo.idm.oclc.org/", url=urllib.parse.urlsplit(cano_url).path
            )

        return (driver, fmt_url_func)

    def _pass2sciencedirect(self, driver: WebDriver, **gatewaykwargs) -> T_PASSTHROGU_JOURNAL:
        def fmt_url_func(cano_url: str, *args, **kwargs) -> str:
            return urllib.parse.urljoin(
                base="https://www-sciencedirect-com.utokyo.idm.oclc.org/", url=urllib.parse.urlsplit(cano_url).path
            )

        return (driver, fmt_url_func)

    def _pass2springer(self, driver: WebDriver, **gatewaykwargs) -> T_PASSTHROGU_JOURNAL:
        def fmt_url_func(cano_url: str, *args, **kwargs) -> str:
            return urllib.parse.urljoin(
                base="https://link-springer-com.utokyo.idm.oclc.org/", url=urllib.parse.urlsplit(cano_url).path
            )

        return (driver, fmt_url_func)

    def _pass2wileyonlinelibrary(self, driver: WebDriver, **gatewaykwargs) -> T_PASSTHROGU_JOURNAL:
        def fmt_url_func(cano_url: str, *args, **kwargs) -> str:
            return urllib.parse.urljoin(
                base="https://onlinelibrary-wiley-com.utokyo.idm.oclc.org/", url=urllib.parse.urlsplit(cano_url).path
            )

        return (driver, fmt_url_func)

    def _pass2ieeexplore(self, driver: WebDriver, **gatewaykwargs) -> T_PASSTHROGU_JOURNAL:
        def fmt_url_func(cano_url: str, *args, **kwargs) -> str:
            return urllib.parse.urljoin(
                base="https://ieeexplore-ieee-org.utokyo.idm.oclc.org/Xplore/home.jsp",
                url=urllib.parse.urlsplit(cano_url).path,
            )

        return (driver, fmt_url_func)

    def _pass2oxfordacademic(self, driver: WebDriver, **gatewaykwargs) -> T_PASSTHROGU_JOURNAL:
        def fmt_url_func(cano_url: str, *args, **kwargs) -> str:
            return urllib.parse.urljoin(
                base="https://academic-oup-com.utokyo.idm.oclc.org/journals", url=urllib.parse.urlsplit(cano_url).path
            )

        return (driver, fmt_url_func)

    def _pass2rscpublishing(self, driver: WebDriver, **gatewaykwargs) -> T_PASSTHROGU_JOURNAL:
        def fmt_url_func(cano_url: str, *args, **kwargs) -> str:
            return urllib.parse.urljoin(
                base="https://pubs-rsc-org.utokyo.idm.oclc.org/", url=urllib.parse.urlsplit(cano_url).path
            )

        return (driver, fmt_url_func)

    def _pass2nejm(self, driver, **gatewaykwargs) -> T_PASSTHROGU_JOURNAL:
        def fmt_url_func(cano_url: str, *args, **kwargs) -> str:
            return urllib.parse.urljoin(
                base="https://www-nejm-org.utokyo.idm.oclc.org/", url=urllib.parse.urlsplit(cano_url).path
            )

        return (driver, fmt_url_func)

    def _pass2pnas(self, driver: WebDriver, **gatewaykwargs) -> T_PASSTHROGU_JOURNAL:
        def fmt_url_func(cano_url: str, *args, **kwargs) -> str:
            return urllib.parse.urljoin(
                base="https://www-pnas-org.utokyo.idm.oclc.org/", url=urllib.parse.urlsplit(cano_url).path
            )

        return (driver, fmt_url_func)

    # def _pass2scitation(self, driver: WebDriver, **gatewaykwargs) -> T_PASSTHROGU_JOURNAL:
    #     driver.get("https://gateway.itc.u-tokyo.ac.jp/,DanaInfo=www.scitation.org,SSO=U+")
    #     # https://gateway.itc.u-tokyo.ac.jp/,DanaInfo=www.scitation.org,SSL+
    #     current_url: str = driver.current_url
    #     url, *_ = current_url.split(",")

    #     def fmt_url_func(cano_url: str, *args, **kwargs) -> str:
    #         gateway_fmt_url = re.sub(
    #             pattern=r"^https?://((?:aip|www)\.scitation\.org)\/(doi\/.+)\/(.+)$",
    #             repl=rf"{url}\2/,DanaInfo=\1,SSL+\3",
    #             string=cano_url,
    #         )
    #         return gateway_fmt_url

    #     return (driver, fmt_url_func)

    def _pass2iopscience(self, driver, **gatewaykwargs) -> T_PASSTHROGU_JOURNAL:
        driver.get("https://iopscience-iop-org.utokyo.idm.oclc.org/")
        current_url: str = driver.current_url

        def fmt_url_func(cano_url: str, *args, **kwargs) -> str:
            return urllib.parse.urljoin(base=current_url, url=urllib.parse.urlsplit(cano_url).path)

        return (driver, fmt_url_func)

    def _pass2science(self, driver: WebDriver, **gatewaykwargs) -> T_PASSTHROGU_JOURNAL:
        driver.get("https://www-science-org.utokyo.idm.oclc.org/")
        current_url: str = driver.current_url

        def fmt_url_func(cano_url: str, *args, **kwargs) -> str:
            return urllib.parse.urljoin(base=current_url, url=urllib.parse.urlsplit(cano_url).path)

        return (driver, fmt_url_func)

    # def _pass2acspublications(self, driver: WebDriver, **gatewaykwargs) -> T_PASSTHROGU_JOURNAL:
    #     driver.get(
    #         "https://gateway.itc.u-tokyo.ac.jp/action/,DanaInfo=pubs.acs.org,SSL,SSO=U+showPublications?display=journals"
    #     )
    #     # https://gateway.itc.u-tokyo.ac.jp:11030/action/showPublications?pubType=journal
    #     current_url: str = driver.current_url.split("/action")[0]  # https://gateway.itc.u-tokyo.ac.jp:11030

    #     def fmt_url_func(cano_url: str, *args, **kwargs) -> str:
    #         gateway_fmt_url = re.sub(
    #             pattern=r"^https?://pubs\.acs\.org\/(.*)$", repl=rf"{current_url}/\1", string=cano_url
    #         )
    #         return gateway_fmt_url

    #     return (driver, fmt_url_func)


all = TranslationGummyGateWays = {
    "useless": UselessGateWay,
    "utokyo": UTokyoGateWay,
}

get = mk_class_get(
    all_classes=TranslationGummyGateWays,
    gummy_abst_class=[GummyAbstGateWay],
    genre="gateways",
)
