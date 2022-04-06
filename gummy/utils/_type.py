# coding: utf-8
from typing import Any, Callable, Dict, List, Optional, Tuple, TypedDict

from bs4 import BeautifulSoup
from selenium.webdriver.remote.webdriver import WebDriver

T_PASSTHROGU_JOURNAL = Tuple[WebDriver, Callable[[str], str]]
T_NoneType = type(None)

T_FIND_TRANSLATED_BULK = Callable[[BeautifulSoup], str]
T_FIND_TRANSLATED_CORR = Callable[[BeautifulSoup, WebDriver], Tuple[List[str], List[str]]]
T_IS_TRANSLATED_PROPERLY = Callable[[str], bool]
T_SPECIALIZE_LANG_DATA = Tuple[T_FIND_TRANSLATED_BULK, T_FIND_TRANSLATED_BULK, T_IS_TRANSLATED_PROPERLY, str]

T_PAPER_CONTENT = TypedDict(
    "T_PAPER_CONTENS",
    {
        "head": Optional[str],
        "img": Optional[str],
        "subhead": Optional[str],
        "raw": Optional[str],
    },
)
T_PAPER_TITLE_CONTENTS = Tuple[str, List[T_PAPER_CONTENT]]
