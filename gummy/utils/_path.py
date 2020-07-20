#coding: utf-8
import os
from pathlib import Path
from .coloring_utils  import toBLUE

__all__ = [
    "UTILS_DIR", "MODULE_DIR", "TEMPLATES_DIR", "REPO_DIR", "GUMMY_DIR", 
    "DOTENV_PATH",
    "IMG_NOT_FOUND_SRC"
]

UTILS_DIR     = os.path.dirname(os.path.abspath(__file__))      # path/to/gummy/utils
MODULE_DIR    = os.path.dirname(UTILS_DIR)                      # path/to/gummy
TEMPLATES_DIR = os.path.join(MODULE_DIR, "templates")           # path/to/gummy/templates
REPO_DIR      = os.path.dirname(MODULE_DIR)                     # path/to/Translation-Gummy
GUMMY_DIR     = os.path.join(os.path.expanduser('~'), '.gummy') # /Users/<username>/.gummy
# Check whether uid/gid has the write access to DATADIR_BASE
if os.path.exists(GUMMY_DIR) and not os.access(GUMMY_DIR, os.W_OK):
    GUMMY_DIR = os.path.join('/tmp', '.gummy')
if not os.path.exists(GUMMY_DIR):
    os.mkdir(GUMMY_DIR)
    print(f"{toBLUE(GUMMY_DIR)} is created. Downloaded data will be stored here.")
DOTENV_PATH   = os.path.join(GUMMY_DIR, ".env")                 # /Users/<username>/.gummy/.env
if not os.path.exists(DOTENV_PATH):
    Path(DOTENV_PATH).touch()
    print(f"{toBLUE(DOTENV_PATH)} is created. Environment variables should be stored here.")
IMG_NOT_FOUND_SRC = "https://github.com/iwasakishuto/Translation-Gummy/blob/master/image/image-not-found.png?raw=true"
