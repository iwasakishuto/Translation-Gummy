# coding: utf-8
import os
UTILS_DIR = os.path.dirname(os.path.abspath(__file__)) # path/to/gummy/utils
MODULE_DIR = os.path.dirname(UTILS_DIR) # path/to/gummy
TEMPLATES_DIR = os.path.join(MODULE_DIR, "templates") # path/to/gummy/templates
REPO_DIR = os.path.dirname(MODULE_DIR) # path/to/Translation-Gummy

from . import driver_utils

from .driver_utils import DRIVER_TYPE
from .driver_utils import get_driver