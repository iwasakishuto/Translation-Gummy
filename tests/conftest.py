# coding: utf-8
import os
import sys
import pytest
from data import TestData
import warnings
try:
    from gummy.utils._warnings import (GummyImprementationWarning, 
                                       EnvVariableNotDefinedWarning)
except ModuleNotFoundError:
    here     = os.path.abspath(os.path.dirname(__file__))
    REPO_DIR = os.path.dirname(here)
    sys.path.append(REPO_DIR)
    print(f"You didn't install 'Translation-Gummy', so add {REPO_DIR} to search path for modules.")
    from gummy.utils._warnings import (GummyImprementationWarning, 
                                       EnvVariableNotDefinedWarning)

def pytest_addoption(parser):
    parser.addoption("--gummy-warnings", choices=["error", "ignore", "always", "default", "module", "once"], default="ignore")

def pytest_configure(config):
    action = config.getoption("gummy_warnings")
    warnings.simplefilter(action, category=GummyImprementationWarning)
    warnings.simplefilter(action, category=EnvVariableNotDefinedWarning)

@pytest.fixture
def db():
    database = TestData()
    return database