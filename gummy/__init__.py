# coding: utf-8

__copyright__       = "Copyright (C) 2020 Shuto Iwasaki"
__version__         = "3.4.3"
try:
    __VERSION_INFO__
except NameError:
    print(f"Translation-Gummy ver.{__version__}")
    __VERSION_INFO__ = "Output Completed"

__license__         = "MIT"
__author__          = "Shuto Iwasaki"
__author_twitter__  = "https://twitter.com/cabernet_rock"
__author_email__    = "cabernet.rock@gmail.com"
__url__             = "https://github.com/iwasakishuto/Translation-Gummy"

from . import gateways
from . import journals
from . import models
from . import translators
from .models import TranslationGummy