# coding: utf-8
import os
import sys
import warnings

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser

from data import TestData

try:
    from gummy.utils._warnings import EnvVariableNotDefinedWarning, GummyImprementationWarning
except ModuleNotFoundError:
    here = os.path.abspath(os.path.dirname(__file__))
    REPO_DIR = os.path.dirname(here)
    sys.path.append(REPO_DIR)
    print(f"You didn't install 'Translation-Gummy', so add {REPO_DIR} to search path for modules.")
    from gummy.utils._warnings import EnvVariableNotDefinedWarning, GummyImprementationWarning


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(
        "--gummy-warnings", choices=["error", "ignore", "always", "default", "module", "once"], default="ignore"
    )


def pytest_configure(config: Config) -> None:
    action = config.getoption("gummy_warnings")
    warnings.simplefilter(action, category=GummyImprementationWarning)
    warnings.simplefilter(action, category=EnvVariableNotDefinedWarning)


@pytest.fixture
def db():
    database = TestData()
    return database
