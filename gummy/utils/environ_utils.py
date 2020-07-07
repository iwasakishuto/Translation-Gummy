#coding: utf-8
import os
import re
from dotenv import load_dotenv
from kerasy.utils import toBLUE, toGREEN

from . import DOTENV_PATH

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
    env_names = read_environ(dotenv_path).update(kwargs)
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
        print(f"Please set environment variable in {toBLUE(dotenv_path)}")
    return not omission