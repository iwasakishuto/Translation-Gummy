#coding: utf-8
import os
import re
import warnings
from dotenv import load_dotenv

from ._path import DOTENV_PATH
from ._warnings import EnvVariableNotDefinedWarning
from .coloring_utils  import toBLUE, toGREEN

TRANSLATION_GUMMY_ENVNAME_PREFIX = "TRANSLATION_GUMMY"

def where_is_envfile():
    return DOTENV_PATH

def read_environ(dotenv_path=DOTENV_PATH):
    """ Read the environment variables from `dotenv_path` """
    env_names = {}
    if os.path.exists(dotenv_path):
        with open(dotenv_path, mode="r") as f:
            for line in f.readlines():
                for key,val in re.findall(pattern=r'^(.+?)\s?=\s?"?(.+?)"?$', string=line):
                    env_names[key] = val
    return env_names

def write_environ(dotenv_path=DOTENV_PATH, **kwargs):
    """ Overwrite the environment variables written in the existing file (`dotenv_path`) """
    env_names = read_environ(dotenv_path)
    env_names.update(kwargs)
    with open(DOTENV_PATH, mode="w") as f:
        f.writelines([f'{key} = "{val}"\n' for key,val in env_names.items()])

def show_environ(dotenv_path=DOTENV_PATH):
    """ Show environment variables. """
    env_names = read_environ(dotenv_path=dotenv_path)
    for key,val in env_names.items():
        print(f'* {toGREEN(key)} : "{toBLUE(val)}"')

def load_environ(dotenv_path=DOTENV_PATH, env_varnames=[]):
    """
    Load environment variables from `path` file, and return 
    whether every necessary VARNAMES (`env_varnames`) are set. 
    """
    if not os.path.exists(dotenv_path):
        return False
    load_dotenv(dotenv_path=dotenv_path)

    omission = False
    for env_name in env_varnames:
        if os.getenv(env_name) is None:
            omission = True
            print(f"{toGREEN(env_name)} is not set.")
    if omission:
        warnings.warn(message=f"Please set environment variable in {toBLUE(dotenv_path)}", category=EnvVariableNotDefinedWarning)
    return not omission

def check_environ(required_kwargs, required_env_varnames=None, verbose=1, **kwargs):
    """
    Check whether meet the requirements.
    @params required_zip    : (zip) zip(required_kwargs, required_env_varnames)
        * required_kwargs       : (list) required kwargs
        * required_env_varnames : (list) required environment variables.
    @return is_ok           : (bool) Whether meet the requirements.
    @return not_meet_kwargs : (list) contains keywords you have to supply.
    """
    if required_env_varnames is None:
        required_env_varnames = [
            f"{TRANSLATION_GUMMY_ENVNAME_PREFIX}_<CLASS_NAME>_<FUNC_NAME>_{kwarg.upper()}"
            for kwarg in required_kwargs
        ]
    not_meet_kwargs = []
    for kwarg,env_name in zip(required_kwargs, required_env_varnames):
        if (kwarg not in kwargs) and (os.getenv(env_name) is None):
            not_meet_kwargs.append(kwarg)
            if verbose>0: print(f"Please set {toGREEN(env_name)} or pass {toBLUE(kwarg)} as kwarg.")
    return len(not_meet_kwargs)==0, not_meet_kwargs
