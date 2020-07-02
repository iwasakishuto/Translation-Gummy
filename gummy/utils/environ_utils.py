#coding: utf-8
import os
from dotenv import load_dotenv
from kerasy.utils import toBLUE, toGREEN

from . import DOTENV_PATH

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

def where_is_envfile():
    print(DOTENV_PATH)

def arrange_kwargs(prefix_="TRANSLATION_GUMMY_GATEWAY_", except_alias_=[], **kwargs):
    if isinstance(except_alias_, str):
        except_alias_ = [except_alias_]
    ALLOWED_ALIASES = [varname.replace(prefix_, "").lower() for varname in ENV_VARNAMES]
    ALLOWED_ALIASES = [alias for alias in ALLOWED_ALIASES if alias not in except_alias_]
    arranged_kwargs = {alias : kwargs.get(alias) or os.getenv(prefix_ + alias.upper()) for alias in ALLOWED_ALIASES}
    return arranged_kwargs

def popkwargs(alias, default=None, kwargs={}, verbose=1):
    # === <START: FOR DEVELOPERS> ===
    msg = ""
    if alias not in kwargs:
        msg += f"You don't specify {toBLUE(alias)} by kwargs"
        ENV_ALIAS = TRANSLATION_GUMMY_PREFIX+alias.upper()
        if ENV_ALIAS not in os.environ:
            msg += f", and you also don't define {toBLUE(ENV_ALIAS)} in environment variables, so use default value."
        else:
            msg += f", but you define {toBLUE(ENV_ALIAS)} in environment variables, so use this value."
    else:
        msg += f"You specify {toBLUE(alias)} by kwargs, so pop the {toBLUE(alias)} from kwargs, and use this value."
    if verbose>0:
        print(msg)
    # === <END: FOR DEVELOPERS> ===
    return kwargs.pop(alias, os.getenv(TRANSLATION_GUMMY_PREFIX+alias.upper(), default))
        
def load_environ(dotenv_path=DOTENV_PATH):
    """
    Load environment variable from `path` file, and return 
    whether every necessary VARNAMES (`ENV_VARNAMES`) are set. 
    """
    if not os.path.exists(dotenv_path):
        return False
    load_dotenv(dotenv_path=dotenv_path)

    omission = False
    for env_name in ENV_VARNAMES:
        if os.getenv(env_name) is None:
            omission = True
            print(f"{toGREEN(env_name)} is not set.")
    if omission:
        print(f"Please set environment variable in {toBLUE(dotenv_path)}")
    return not omission