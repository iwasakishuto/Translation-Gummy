# coding: utf-8
import os
from kerasy.utils import toBLUE

UTILS_DIR = os.path.dirname(os.path.abspath(__file__)) # path/to/gummy/utils
MODULE_DIR = os.path.dirname(UTILS_DIR)                # path/to/gummy
TEMPLATES_DIR = os.path.join(MODULE_DIR, "templates")  # path/to/gummy/templates
REPO_DIR = os.path.dirname(MODULE_DIR)                 # path/to/Translation-Gummy
ENV_PATH = os.path.join(MODULE_DIR, ".env")            # path/to/gummy/.env
DOWNLOAD_DIR = os.path.join(os.path.expanduser('~'), '.gummy') # /Users/<username>/.gummy
# Check whether uid/gid has the write access to DATADIR_BASE
if os.path.exists(DOWNLOAD_DIR) and not os.access(DOWNLOAD_DIR, os.W_OK):
    DOWNLOAD_DIR = os.path.join('/tmp', '.gummy')
if not os.path.exists(DOWNLOAD_DIR):
    os.mkdir(DOWNLOAD_DIR)
    print(f"{toBLUE(DOWNLOAD_DIR)} is created. Downloaded data will be stored here.")

from . import compress_utils
from . import download_utils
from . import driver_utils
from . import environ_utils
from . import gateway_utils
from . import generic_utils

from .download_utils import readable_size
from .download_utils import decide_extension
from .download_utils import download_file

from .driver_utils import DRIVER_TYPE
from .driver_utils import get_driver

from .environ_utils import load_environ

from .gateway_utils import pass_gate_way

from .generic_utils import recreate_dir

from .compress_utils import recreate_dir
from .compress_utils import is_compressed
from .compress_utils import extract_from_compressed
from .compress_utils import extract_from_zip
from .compress_utils import extract_from_tar
