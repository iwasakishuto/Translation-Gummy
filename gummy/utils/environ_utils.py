#coding: utf-8
import os
from dotenv import load_dotenv
from kerasy.utils import toBLUE, toGREEN

from . import ENV_PATH

TRANSLATION_GUMMY_PREFIX = "TRANSLATION_GUMMY_"
ENV_VARNAMES = [
    "TRANSLATION_GUMMY_GATEWAY_URL",
    "TRANSLATION_GUMMY_GATEWAY_USERNAME",
    "TRANSLATION_GUMMY_GATEWAY_PASSWORD",
    "TRANSLATION_GUMMY_GATEWAY_SUBMIT_ID",
    "TRANSLATION_GUMMY_GATEWAY_CONFIRM_ID",
    "TRANSLATION_GUMMY_GATEWAY_URL_FORMAT",
]
ENV_ALIASES = [varname.replace(TRANSLATION_GUMMY_PREFIX, "").lower() for varname in ENV_VARNAMES]

def arrange_kwargs(prefix_="TRANSLATION_GUMMY_GATEWAY_", **kwargs):
    ALLOWED_ALIASES = [varname.replace(prefix_, "").lower() for varname in ENV_VARNAMES]
    arranged_kwargs = {alias : kwargs.get(alias) or os.getenv(prefix_ + alias.upper()) for alias in ALLOWED_ALIASES}
    return arranged_kwargs

def popkwargs(alias, default=None, kwargs={}):
    return kwargs.pop(alias, os.getenv(TRANSLATION_GUMMY_PREFIX+alias.upper(), default))
        
def load_environ(path=ENV_PATH):
    """
    Load environment variable from `path` file, and return 
    whether every necessary VARNAMES (`ENV_VARNAMES`) are set. 
    """
    if not os.path.exists(path):
        return False
    load_dotenv(dotenv_path=path)

    omission = False
    for env_name in ENV_VARNAMES:
        if os.getenv(env_name) is None:
            omission = True
            print(f"{toGREEN(env_name)} is not set.")
    if omission:
        print(f"Please set environment variable in {toBLUE(path)}")
    return not omission