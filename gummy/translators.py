# coding: utf-8
"""These classes translate English(``from_lang``) into Japanese(``to_lang``) using an external 
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
from collections import defaultdict
from bs4 import BeautifulSoup

from .utils._data import lang_code2name, lang_name2code
from .utils.coloring_utils import toBLUE, toGREEN
from .utils.driver_utils import get_driver
from .utils.generic_utils import handleKeyError, handleTypeError, mk_class_get, splitted_query_generator
from .utils.monitor_utils import ProgressMonitor
from .utils.soup_utils import find_target_text, find_all_target_text

class GummyAbstTranslator(metaclass=ABCMeta):
    def __init__(self, driver=None, maxsize=5000, interval=1, trials=30, verbose=False, use_cache=True, specialize=True, from_lang="en", to_lang="ja"):
        """If you want to create your own translator class, please inherit this class.

        Args:
            driver (WebDriver) : Selenium WebDriver.
            maxsize (int)      : Number of English characters that we can send a request at one time. (default= ``5000``)
            interval (int)     : Trial interval [s]. (default= ``1``)
            trials (int)       : How many times to try to find translated text. (default= ``30``)
            verbose (bool)     : Whether to print message or not. (default= ``False``)
            use_cache (bool)   : Whether to use cache or not. cashe is used in :meth:`is_translated <gummy.translators.GummyAbstTranslator.is_translated>` (default= ``True``)
            specialize (bool)  : Whether to support multiple languages or specialize. (default= ``True``) If you want to specialize in translating between specific languages, set ``from_lang`` and ``to_lang`` arguments.
            from_lang (str)    : Language before translation.
            to_lang (str)      : Language after translation.


        Attributes:
            cache (str) : Translated text acquired one time ago. Prevent bugs where the same translated text is repeated. Used in :meth:`is_translated <gummy.translators.GummyAbstTranslator.is_translated>`.
        """
        self.driver = driver
        self.maxsize = maxsize
        self.interval = interval
        self.trials = trials
        self.verbose = verbose
        self.use_cache = use_cache
        self.cache = ""
        self.setup(specialize=specialize, from_lang=from_lang, to_lang=to_lang)

    @property
    def class_name(self):
        """Same as ``self.__class__.__name__``."""
        return self.__class__.__name__

    @property
    def name(self):
        """Translator service name."""
        return self.class_name.replace("Translator", "")

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

    def check_driver(self, driver=None):
        """If the driver does not exist, use :meth:`get_driver <gummy.utils.driver_utils.get_driver>` to get the driver."""
        driver = driver or self.driver
        if driver is None:
            driver = get_driver()
        self.driver = driver
        # if self.verbose: print(f"Driver info:\n{json.dumps(self.driver_info, indent=2)}")
        return driver

    def setup(self, specialize=True, from_lang="en", to_lang="ja"):
        """Setup an instance by defining a required translation methods.

        Args:
            specialize (bool)  : Whether to support multiple languages or specialize. (default= ``True``) If you want to specialize in translating between specific languages, set ``from_lang`` and ``to_lang`` arguments.
        """
        self.url_fmt = ""
        self.lang2args = defaultdict(lambda: defaultdict(list))
        if specialize:
            self.register_method(from_lang=from_lang, to_lang=to_lang)
            self.find_translated, self.is_translated_properly, self.url_fmt = self.lang2args[from_lang][to_lang]
        else:
            for from_lang, to_lang, kwargs in self.generate_lang_pairs():
                self.register_method(from_lang=from_lang, to_lang=to_lang, **kwargs)
        self.specialize = specialize

    @abstractproperty
    def supported_langs(self):
        """Supported language codes."""
        return []

    @abstractmethod
    def specialize2langs(self, from_lang, to_lang, **kwargs):
        """Create the functions and variables needed to translate from ``from_lang`` to ``to_lang``

        Args:
            specialize (bool)  : Whether to support multiple languages or specialize. (default= ``True``) If you want to specialize in translating between specific languages, set ``from_lang`` and ``to_lang`` arguments.

        Return:
            tuple (func, func, str): Tuple of elements required in :meth:`register_method <gummy.translators.GummyAbstTranslator.register_method>` 
                - :meth:`find_translated <gummy.translators.GummyAbstTranslator.find_translated>`  (func): Find translated text from ``soup``
                - ``is_translated_properly`` (func): Check if the acquired translated_text is appropriate.
                - ``url_fmt`` (str): "{query}" must be included.
        """
        url_fmt = f"https://domain/{from_lang}2{to_lang}/?query=" + "{query}"
        return (self.find_translated, self.is_translated_properly, url_fmt)

    def generate_lang_pairs(self):
        """Generator to generate all translation pairs."""
        for from_lang in self.supported_langs:
            for to_lang in self.supported_langs:
                yield (from_lang, to_lang, {})

    def register_method(self, from_lang, to_lang, **kwargs):
        """Register Methods which translate ``from_lang`` to ``to_lang``

        Args:
            from_lang (str)    : Language before translation.
            to_lang (str)      : Language after translation.
            kwargs (dict)      : kwargs required for :meth:`specialize2langs <gummy.translators.GummyAbstTranslator.specialize2langs>`.
        """
        from_lang = lang_name2code.get(from_lang, "en")
        to_lang   = lang_name2code.get(to_lang,   "ja")
        find_translated, is_translated_properly, url_fmt = self.specialize2langs(from_lang, to_lang, **kwargs)
        self.lang2args[from_lang][to_lang] = [find_translated, is_translated_properly, url_fmt]
        method_name = f"{from_lang}2{to_lang}"
        method = lambda query, driver=None, barname=None : self._translate(query=query, find_translated=find_translated, is_translated_properly=is_translated_properly, url_fmt=url_fmt, driver=driver, barname=barname)
        setattr(self, method_name, method)

    def translate(self, query, driver=None, barname=None, from_lang="en", to_lang="ja"):
        """Translate English into Japanese.

        Args:
            query (str)        : English to be translated.
            driver (WebDriver) : Selenium WebDriver.
            barname (str)      : Bar name for :meth:`ProgressMonitor <gummy.utils.monitor_utils.ProgressMonitor>`.
            from_lang (str)    : Language before translation.
            to_lang (str)      : Language after translation.

        Examples:
            >>> from gummy import translators
            >>> # Support multiple languages.
            >>> translator = translators.get("deepl", specialize=False, verbose=True)
            >>> ja = translator.translate(query="This is a pen.", from_lang="en", to_lang="ja")
            DeepLTranslator (query1) 02/30 [#-------------------]  6.67% - 2.140[s]
            >>> print(ja)
            これはペンです。
            >>> fr = translator.translate(query="This is a pen.", from_lang="en", to_lang="fr")
            DeepLTranslator (query1) 01/30 [--------------------]  3.33% - 1.068[s]
            >>> print(fr)
            C'est un stylo.
            >>> # Specialize
            >>> translator = translators.get("deepl", specialize=True, from_lang="en", to_lang="ja", verbose=True)
            >>> ja = translator.translate(query="This is a pen.")
            DeepLTranslator (query1) 03/30 [##------------------] 10.00% - 3.227[s]
            >>> print(ja)
            これはペンです。
            >>> fr = translator.translate(query="This is a pen.", from_lang="en", to_lang="fr")
            DeepLTranslator (query1) 03/30 [##------------------] 10.00% - 3.220[s]
            >>> print(fr)
            これはペンです。
        """
        if self.specialize:
            find_translated = self.find_translated
            is_translated_properly = self.is_translated_properly
            url_fmt = self.url_fmt
        else:
            handleKeyError(lst=list(self.lang2args.keys()), from_lang=from_lang)
            handleKeyError(lst=list(self.lang2args[from_lang].keys()), to_lang=to_lang)
            find_translated, is_translated_properly, url_fmt = self.specialize2langs(from_lang, to_lang)
        return self._translate(query=query, find_translated=find_translated, is_translated_properly=is_translated_properly, url_fmt=url_fmt, driver=driver, barname=barname)

    def _translate(self, query, find_translated, is_translated_properly, url_fmt, driver=None, barname=None):
        """A translating function running in :meth:`translate <gummy.translators.GummyAbstTranslator.translate>` """
        driver = self.check_driver(driver=driver)
        maxsize = self.maxsize
        interval = self.interval
        trials = self.trials
        verbose = self.verbose
        barname = barname or self.class_name

        translated_texts = []
        gen = splitted_query_generator(query=query, maxsize=maxsize)
        for i,q in enumerate(gen):
            url = url_fmt.format(query=urllib.parse.quote(q))
            driver.refresh()
            driver.get(url)
            monitor = ProgressMonitor(max_iter=trials, verbose=verbose, barname=f"{barname} (query{i+1})")
            for i in range(trials):
                time.sleep(interval)
                soup = BeautifulSoup(markup=driver.page_source.encode("utf-8"), features="lxml")
                translated_text = find_translated(soup)
                monitor.report(i, translated=translated_text[:5])
                if is_translated_properly(translated_text): break                
            monitor.remove()
            translated_texts.append(translated_text)
            if self.use_cache: self.cache = translated_text
            time.sleep(1)        
        return "".join(translated_texts)

    @abstractstaticmethod
    def find_translated(soup):
        """Find translated Translated text from ``soup``

        Args:
            soup (bs4.BeautifulSoup): A data structure representing a parsed HTML or XML document.

        Return:
            str: Translated text.
        """
        return find_target_text(soup=soup, name="japanese")

    def is_translated_properly(self, translated_text):
        """Check if the acquired translated_text is appropriate.

        Args:
            translated_text (str) : Translated text.
        
        Examples:
            >>> from gummy import translators
            >>> translator = translators.get("google", specialize=True, from_lang="en", to_lang="ja")
            >>> translator.is_translated_properly("")
            False
            >>> translator.is_translated_properly("日本語")
            True
            >>> translator.cache = "日本語"
            >>> translator.is_translated_properly("日本語")
            False
        """
    def is_translated_properly(self, translated_text):
        return (len(translated_text)>0) and (not self.cache.startswith(translated_text))

class DeepLTranslator(GummyAbstTranslator):
    """
    DeepL is a deep learning company that develops artificial intelligence systems 
    for languages. See https://www.deepl.com/en/home for more info.
    """
    def __init__(self, driver=None, maxsize=5000, interval=1, trials=30, verbose=False, use_cache=True, specialize=True, from_lang="en", to_lang="ja"):
        super().__init__(driver=driver, maxsize=maxsize, interval=interval, trials=trials, verbose=verbose, use_cache=use_cache, specialize=specialize, from_lang=from_lang, to_lang=to_lang)

    @property
    def supported_langs(self):
        return ['de', 'es', 'en', 'fr', 'it', 'ja', 'nl', 'pl', 'pt', 'ru', 'zh']

    @staticmethod
    def find_translated(soup):
        return find_target_text(soup=soup, name="button", class_="lmt__translations_as_text__text_btn")

    def specialize2langs(self, from_lang, to_lang, **kwargs):
        url_fmt = f"https://www.deepl.com/en/translator#{from_lang}/{to_lang}/" + "{query}"
        return (self.find_translated, self.is_translated_properly, url_fmt)

    def is_translated_properly(self, translated_text):
        """Deepl represents the character being processed as ``[...]``, so make sure it has not completed.
        
        Examples:
            >>> from gummy import translators
            >>> translator = translators.get("deepl")
            >>> translator.is_translated_properly("日本語 [...]")
            False
            >>> translator.is_translated_properly("[...]日本語")
            True
            >>> translator.is_translated_properly("日本語[...]日本語")
            True
        """
        return super().is_translated_properly(translated_text) and (not translated_text.endswith("[...]"))

class GoogleTranslator(GummyAbstTranslator):
    """Google Translate is a free multilingual neural machine translation service 
    developed by Google, to translate text and websites from one language into 
    another. See https://translate.google.com/ for more info.
    """
    def __init__(self, driver=None, maxsize=5000, interval=1, trials=30, verbose=False, use_cache=True, specialize=True, from_lang="en", to_lang="ja"):
        super().__init__(driver=driver, maxsize=maxsize, interval=interval, trials=trials, verbose=verbose, use_cache=use_cache, specialize=specialize, from_lang=from_lang, to_lang=to_lang)

    @property
    def supported_langs(self):
        return ['af', 'am', 'ar', 'az', 'be', 'bg', 'bn', 'bs', 'ca', 'co', 'cs', 'cy', 'da', 'de', 'el', 'en', 'eo', 'es', 'et', 'eu', 'fa', 'fi', 'fr', 'fy', 'ga', 'gd', 'gl', 'gu', 'ha', 'hi', 'hr', 'ht', 'hu', 'hy', 'id', 'ig', 'is', 'it', 'iw', 'ja', 'jw', 'ka', 'kk', 'km', 'kn', 'ko', 'ku', 'ky', 'la', 'lb', 'lo', 'lt', 'lv', 'mg', 'mi', 'mk', 'ml', 'mn', 'mr', 'ms', 'mt', 'my', 'ne', 'nl', 'no', 'ny', 'or', 'pa', 'pl', 'ps', 'pt', 'ro', 'ru', 'rw', 'sd', 'si', 'sk', 'sl', 'sm', 'sn', 'so', 'sq', 'sr', 'st', 'su', 'sv', 'sw', 'ta', 'te', 'tg', 'th', 'tk', 'tl', 'tr', 'tt', 'ug', 'uk', 'ur', 'uz', 'vi', 'xh', 'yi', 'yo', 'zh', 'zu']

    @staticmethod
    def find_translated(soup):
        return find_all_target_text(soup=soup, name="span", attrs={"jsname": "W297wb"}, joint="")

    def specialize2langs(self, from_lang, to_lang, **kwargs):
        url_fmt = f"https://translate.google.co.jp/#{from_lang}/{to_lang}/".replace("zh", "zh-CN") + "{query}"
        return (self.find_translated, self.is_translated_properly, url_fmt)

all = TranslationGummyTranslators = {
    "google" : GoogleTranslator,
    "deepl"  : DeepLTranslator,
}

get = mk_class_get(
    all_classes=TranslationGummyTranslators,
    gummy_abst_class=[GummyAbstTranslator],
    genre="translators",
)