# coding: utf-8
import sys

__copyright__    = "Copyright (C) 2020 Shuto Iwasaki"
__version__      = "0.1.2"

__license__      = "MIT"
__author__       = "Shuto Iwasaki"
__author_email__ = "cabernet.rock@gmail.com"
__url__          = "https://github.com/iwasakishuto/Translation-Gummy"

from . import cli
from . import gateways
from . import journals
from . import models
from . import translators
from .cli import translate_journal
from .cli import translate_text
from .models import TranslationGummy