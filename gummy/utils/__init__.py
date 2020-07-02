# coding: utf-8
import os
from pathlib import Path
from kerasy.utils import toBLUE

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

class GummyImprementationWarning(Warning):
    """ 
    Warnings that developers will resolve. 
    Developers are solving in a simple stupid way.
    """
    pass

from . import compress_utils
from . import download_utils
from . import driver_utils
from . import environ_utils
from . import gateway_utils
from . import generic_utils
from . import outfmt_utils

from .download_utils import readable_size
from .download_utils import decide_extension
from .download_utils import download_file

from .driver_utils import DRIVER_TYPE
from .driver_utils import get_driver

from .environ_utils import TRANSLATION_GUMMY_PREFIX, ENV_VARNAMES, ENV_ALIASES
from .environ_utils import where_is_envfile
from .environ_utils import arrange_kwargs
from .environ_utils import popkwargs
from .environ_utils import load_environ

from .gateway_utils import pass_gate_way

from .generic_utils import print_log
from .generic_utils import recreate_dir

from .compress_utils import recreate_dir
from .compress_utils import is_compressed
from .compress_utils import extract_from_compressed
from .compress_utils import extract_from_zip
from .compress_utils import extract_from_tar

from .outfmt_utils import get_jinja_all_attrs
from .outfmt_utils import check_contents
from .outfmt_utils import tohtml
from .outfmt_utils import html2pdf
from .outfmt_utils import toPDF