# coding: utf-8
from ast import Num
from numbers import Number
from typing import Any, Callable, Dict, List, Optional, Tuple, TypedDict, Union

from bs4 import BeautifulSoup
from selenium.webdriver.remote.webdriver import WebDriver

T_PASSTHROGU_JOURNAL = Tuple[WebDriver, Callable[[str], str]]
T_NoneType = type(None)

T_FIND_TRANSLATED_BULK = Callable[[BeautifulSoup], str]
T_FIND_TRANSLATED_CORR = Callable[[BeautifulSoup, WebDriver], Tuple[List[str], List[str]]]
T_IS_TRANSLATED_PROPERLY = Callable[[str], bool]
T_SPECIALIZE_LANG_DATA = Tuple[T_FIND_TRANSLATED_BULK, T_FIND_TRANSLATED_BULK, T_IS_TRANSLATED_PROPERLY, str]

T_TRANSLATION_CONTENT = TypedDict(
    "T_PAPER_CONTENS",
    {
        "raw": Optional[str],
        "translated": Optional[str],
    },
)

T_IMAGE_CONTENT = TypedDict("T_IMAGE_CONTENT", {"src": Optional[str], "caption": Optional[T_TRANSLATION_CONTENT]})

T_PAPER_CONTENT = TypedDict(
    "T_PAPER_CONTENS",
    {
        "head": Optional[str],
        "subhead": Optional[str],
        "img": Optional[T_IMAGE_CONTENT],
        "body": Optional[T_TRANSLATION_CONTENT],
    },
)
T_PAPER_TITLE_CONTENTS = Tuple[str, List[T_PAPER_CONTENT]]

T_FORM_ACTION = TypedDict(
    "T_FORM_ACTION",
    {
        "action": Optional[Union[str, callable]],
        "by": Optional[str],
        "identifier": Optional[str],
        "values": Optional[Union[str, Number]],
    },
)
