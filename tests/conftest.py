# coding: utf-8
import sys
import warnings
from gummy.utils import GummyImprementationWarning

def pytest_addoption(parser):
    parser.addoption("--gummy-warnings", choices=["error", "ignore", "always", "default", "module", "once"], default="ignore")

def pytest_configure(config):
    action = config.getoption("gummy_warnings")
    warnings.simplefilter(action, category=GummyImprementationWarning)
