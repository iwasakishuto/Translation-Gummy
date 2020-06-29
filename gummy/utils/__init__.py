# coding: utf-8
import os
UTILS_DIR = os.path.dirname(os.path.abspath(__file__)) # path/to/gummy/utils
MODULE_DIR = os.path.dirname(UTILS_DIR) # path/to/gummy
TEMPLATES_DIR = os.path.join(MODULE_DIR, "templates") # path/to/gummy/templates
REPO_DIR = os.path.dirname(MODULE_DIR) # path/to/Translation-Gummy
ENV_PATH = os.path.join(MODULE_DIR, ".env")

from . import driver_utils
from . import gateway_utils

from .driver_utils import DRIVER_TYPE
from .driver_utils import get_driver

from .gateway_utils import pass_gate_way