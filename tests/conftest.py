# coding: utf-8
import os
import sys
import pytest
from sentences import Sentences
import warnings
try:
    from gummy.utils import GummyImprementationWarning
except ModuleNotFoundError:
    here     = os.path.abspath(os.path.dirname(__file__))
    REPO_DIR = os.path.dirname(here) 
    sys.path.append(REPO_DIR)
    print(f"You didn't install 'Translation-Gummy', so add {REPO_DIR} to search path for modules.")
    from gummy.utils import GummyImprementationWarning

def pytest_addoption(parser):
    parser.addoption("--gummy-warnings", choices=["error", "ignore", "always", "default", "module", "once"], default="ignore")

def pytest_configure(config):
    action = config.getoption("gummy_warnings")
    warnings.simplefilter(action, category=GummyImprementationWarning)

@pytest.fixture
def db():
    sentences_db = Sentences()
    return sentences_db