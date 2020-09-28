# coding: utf-8
"""These classes translate English into Japanese using an external 
translation service (website).

Currently, Translation-Gummy supports the following services:
    - `Google Translate <https://translate.google.co.jp/#en/ja/Translation%20Gummy>`_
    - `DeepL Translator <https://www.deepl.com/en/translator#en/ja/Translation%20Gummy>`_

You can easily get (import) ``Translator Class`` by the following ways.

.. code-block:: python

    >>> from gummy import translators
    >>> translator = translators.get("google")
    >>> translator
    <gummy.translators.GoogleTranslator at 0x129890160>
    >>> from gummy.translators import GoogleTranslator
    >>> google = GoogleTranslator()
    >>> google
    <gummy.translators.GoogleTranslator at 0x129890700>
    >>> translator = translators.get(google)
    >>> id(google) == id(translator)
    True
"""
import re
import time
import json
import urllib
import warnings
from abc import ABCMeta, abstractmethod, abstractproperty, abstractstaticmethod
from bs4 import BeautifulSoup

from .utils.coloring_utils import toBLUE, toGREEN
from .utils.driver_utils import get_driver
from .utils.generic_utils import handleKeyError, handleTypeError, mk_class_get, splitted_query_generator
from .utils.monitor_utils import ProgressMonitor
from .utils.soup_utils import find_target_text

class GummyAbstTranslator(metaclass=ABCMeta):
    def __init__(self, driver=None, maxsize=5000, interval=1, trials=30, verbose=False, use_cache=True):
        """If you want to create your own translator class, please inherit this class.

        Args:
            driver (WebDriver) : Selenium WebDriver.
            maxsize (int)      : Number of English characters that we can send a request at one time. (default= ``5000``)
            interval (int)     : Trial interval [s]. (default= ``1``)
            trials (int)       : How many times to try to find japanese text. (default= ``30``)
            verbose (bool)     : Whether to print message or not. (default= ``False``)
            use_cache (bool)   : Whether to use cache or not. cashe is used in :meth:`is_ja_enough <gummy.translators.GummyAbstTranslator.is_ja_enough>` (default= ``True``)

        Attributes:
            cache_ja (str) : Japanese acquired one time ago. Prevent bugs where the same Japanese is repeated. Used in :meth:`is_ja_enough <gummy.translators.GummyAbstTranslator.is_ja_enough>`.
        """
        self.driver = driver
        self.maxsize = maxsize
        self.interval = interval
        self.trials = trials
        self.verbose = verbose
        self.use_cache = use_cache
        self.cache_ja = ""

    @property
    def class_name(self):
        """Same as ``self.__class__.__name__``."""
        return self.__class__.__name__

    @property
    def name(self):
        """Translator service name."""
        return self.class_name.replace("Translator", "")

    @abstractproperty
    def en2ja_url_fmt(self):
        """Format of the query. English will be assigned to ``{english}``."""
        return "https://domain/english2japanese/?query={english}"

    @abstractstaticmethod
    def find_ja(soup):
        """Find translated Japanese text from ``soup``

        Args:
            soup (bs4.BeautifulSoup): A data structure representing a parsed HTML or XML document.

        Return:
            str: Japanese text.
        """
        return find_target_text(soup=soup, name="japanese")

    def is_ja_enough(self, ja):
        """Check if the acquired Japanese is appropriate

        Args:
            ja (str) : Translated Japanese text.
        
        Examples:
            >>> from gummy import translators
            >>> translator = translators.get("google")
            >>> translator.is_ja_enough("")
            False
            >>> translator.is_ja_enough("日本語")
            True
            >>> translator.cache_ja = "日本語"
            >>> translator.is_ja_enough("日本語")
            False
        """
        return (len(ja)>0) and (not self.cache_ja.startswith(ja))

    @property
    def driver_info(self):
        """Return driver_info

        Examples:
            >>> from gummy.utils import get_driver
            >>> from gummy.translators import GoogleTranslator
            >>> with get_driver() as driver:
            ...     translator = GoogleTranslator(driver=driver)
            ...     print(translator.driver_info)
            {'session_id': '3e869e62f06c5f7d938831179ad3c50e', 'browserName': 'chrome'}
            >>> translator = GoogleTranslator(driver=None)
            >>> print(translator.driver_info)
            {}
        """
        info = {}
        driver = self.driver
        if driver is not None:
            info["session_id"] = driver.session_id
            info["browserName"] = driver.capabilities.get("browserName")
        return info

    def check_en2ja(self):
        """Make sure :meth:`en2ja_url_fmt <gummy.translators.GummyAbstTranslator.en2ja_url_fmt>` is appropriate.

        Raises:
            TypeError  : When ``self.en2ja_url_fmt`` is not ``str`` type.
            ValueError : When ``{english}`` not in ``self.en2ja_url_fmt``.
        """
        # en2ja format.
        if not isinstance(self.en2ja_url_fmt, str):
            raise TypeError(f"`self.en2ja_url_fmt` must be str not {type(self.en2ja_url_fmt)}")
        if self.en2ja_url_fmt.find("{english}") == -1:
            raise ValueError("Please include {english} in `self.en2ja_url_fmt`")

    def check_driver(self, driver=None):
        """If the driver does not exist, use :meth:`get_driver <gummy.utils.driver_utils.get_driver>` to get the driver."""
        driver = driver or self.driver
        if driver is None:
            driver = get_driver()
        self.driver = driver
        if self.verbose: print(f"Driver info:\n{json.dumps(self.driver_info, indent=2)}")
        return driver

    def en2ja(self, query, driver=None, barname=None):
        """Translate English into Japanese.

        Args:
            query (str)        : English to be translated.
            driver (WebDriver) : Selenium WebDriver.
            barname (str)      : Bar name for :meth:`ProgressMonitor <gummy.utils.monitor_utils.ProgressMonitor>`.

        Examples:
            >>> from gummy.translators import GoogleTranslator
            >>> ja = translator.en2ja("This is a pen.")
            GoogleTranslator (query1) 01/30 [--------------------]  3.33% - 2.731[s]
            >>> print(ja)
            これはペンです。
            >>> ja = translator.en2ja("This is a pen.", barname="^_^")
            ^_^ (query1) 30/30 [####################]100.00% - 81.073[s]
            >>> print(ja)
            これはペンです。
            >>> # The reason why it takes a long time above is that the same Japanese is repeated.
            >>> translator.cache_ja = ""
            >>> ja = translator.en2ja("This is a pen.", barname="^_^")
            ^_^ (query1) 01/30 [--------------------]  3.33% - 2.725[s]
            >>> print(ja)
            これはペンです。
        """
        self.check_en2ja()
        driver = self.check_driver(driver=driver)
        maxsize = self.maxsize
        interval = self.interval
        trials = self.trials
        verbose = self.verbose
        if barname is None: barname = self.class_name
        
        japanese = []
        gen = splitted_query_generator(query=query, maxsize=maxsize)
        for i,q in enumerate(gen):
            url = self.en2ja_url_fmt.format(english=urllib.parse.quote(q))
            driver.refresh()
            driver.get(url)
            monitor = ProgressMonitor(max_iter=trials, verbose=verbose, barname=f"{barname} (query{i+1})")
            for i in range(trials):
                time.sleep(interval)
                html = driver.page_source.encode("utf-8")
                soup = BeautifulSoup(html, "lxml")
                ja = self.find_ja(soup)
                monitor.report(i, japanese=ja)
                if self.is_ja_enough(ja):
                    break
            monitor.remove()
            japanese.append(ja)
            if self.use_cache:
                self.cache_ja = ja
            time.sleep(1)
        
        japanese = "".join(japanese)
        return japanese

class DeepLTranslator(GummyAbstTranslator):
    """
    DeepL is a deep learning company that develops artificial intelligence systems 
    for languages. See https://www.deepl.com/en/home for more info.
    """
    def __init__(self, driver=None, maxsize=5000, interval=1, trials=30, verbose=False, use_cache=True):
        super().__init__(driver=driver, maxsize=maxsize, interval=interval, trials=trials, verbose=verbose, use_cache=use_cache)

    @property
    def en2ja_url_fmt(self):
        return "https://www.deepl.com/en/translator#en/ja/{english}"

    @staticmethod
    def find_ja(soup):
        return find_target_text(soup=soup, name="button", class_="lmt__translations_as_text__text_btn")

    def is_ja_enough(self, ja):
        """Deepl represents the character being processed as ``[...]``, so make sure it isn't at the end of the japanese.
        
        Examples:
            >>> from gummy import translators
            >>> translator = translators.get("deepl")
            >>> translator.is_ja_enough("日本語 [...]")
            False
            >>> translator.is_ja_enough("[...]日本語")
            True
            >>> translator.is_ja_enough("日本語[...]日本語")
            True
        """
        return super().is_ja_enough(ja) and (not ja.endswith("[...]"))

class GoogleTranslator(GummyAbstTranslator):
    """Google Translate is a free multilingual neural machine translation service 
    developed by Google, to translate text and websites from one language into 
    another. See https://translate.google.com/ for more info.
    """
    def __init__(self, driver=None, maxsize=5000, interval=1, trials=30, verbose=False, use_cache=True):
        super().__init__(driver=driver, maxsize=maxsize, interval=interval, trials=trials, verbose=verbose, use_cache=use_cache)

    @property
    def en2ja_url_fmt(self):
        return "https://translate.google.co.jp/#en/ja/{english}"

    @staticmethod
    def find_ja(soup):
        return find_target_text(soup=soup, name="span", class_="tlid-translation translation", attrs={"lang": "ja"})

all = TranslationGummyTranslators = {
    "google" : GoogleTranslator,
    "deepl"  : DeepLTranslator,
}

get = mk_class_get(
    all_classes=TranslationGummyTranslators,
    gummy_abst_class=[GummyAbstTranslator],
    genre="translators",
)