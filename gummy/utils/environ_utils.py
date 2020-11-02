#coding: utf-8
""" Utility programs for environment variables."""
import os
import re
import warnings
from dotenv import load_dotenv

from ._path import DOTENV_PATH
from ._warnings import EnvVariableNotDefinedWarning
from .coloring_utils  import toBLUE, toGREEN

TRANSLATION_GUMMY_ENVNAME_PREFIX = "TRANSLATION_GUMMY"

def name2envname(name, service="", prefix=""):
    """Convert name to environment varname.

    Args:
        name (str)    : name.
        service (str) : service name. (default= ``""``)
        prefix (str)  : prefix of the ``name``. (default= ``""``)

    Examples:
        >>> from gummy.utils import name2envname
        >>> name2envname(name="name", service="",        prefix="")
        'TRANSLATION_GUMMY_NAME'
        >>> name2envname(name="name", service="service", prefix="")
        'TRANSLATION_GUMMY_SERVICE_NAME'
        >>> name2envname(name="name", service="",        prefix="prefix")
        'TRANSLATION_GUMMY_PREFIX_NAME'
        >>> name2envname(name="name", service="service", prefix="prefix")
        'TRANSLATION_GUMMY_SERVICE_PREFIX_NAME'
    """
    strings = [TRANSLATION_GUMMY_ENVNAME_PREFIX]
    for string in [service, prefix]:
        if len(string)>0:
            strings.append(string)
    strings.append(name)
    return "_".join(strings).upper()

def where_is_envfile():
    """Get Where the envfile is.

    Examples:
        >>> from gummy.utils import where_is_envfile
        >>> where_is_envfile()
        '/Users/iwasakishuto/.gummy/.env'
    """
    return DOTENV_PATH

def read_environ(dotenv_path=DOTENV_PATH):
    """Read the environment variables from ``dotenv_path`` 
    
    Args:
        dotenv_path (str) : path/to/.env (default= ``DOTENV_PATH``)

    Returns:
        dict : the dictionary containing ``dotenv_path``'s environment variables.
    
    Examples:
        >>> from gummy.utils import read_environ
        >>> read_environ()
        {'TRANSLATION_GUMMY_GATEWAY_UTOKYO_USERNAME': 'USERNAME',
        'TRANSLATION_GUMMY_GATEWAY_UTOKYO_PASSWORD': 'PASSWORD'}
    """
    env_variables = {}
    if os.path.exists(dotenv_path):
        with open(dotenv_path, mode="r", encoding='utf-8') as f:
            for line in f.readlines():
                for key,val in re.findall(pattern=r'^(.+?)\s?=\s?"?(.+?)"?$', string=line):
                    env_variables[key] = val
    return env_variables

def write_environ(dotenv_path=DOTENV_PATH, **kwargs):
    """Overwrite or Write the environment variables in ``dotenv_path``
    
    Args:
        dotenv_path (str) : path/to/.env (default= ``DOTENV_PATH``)
        kwargs (dict)     : new environment variables

    Examples:
        >>> from gummy.utils import read_environ, write_environ
        >>> read_environ()
        {'TRANSLATION_GUMMY_GATEWAY_UTOKYO_USERNAME': 'USERNAME',
        'TRANSLATION_GUMMY_GATEWAY_UTOKYO_PASSWORD': 'PASSWORD'}
        >>> write_environ(TRANSLATION_GUMMY_SAMPLE="SAMPLE")
        >>> read_environ()
        {'TRANSLATION_GUMMY_GATEWAY_UTOKYO_USERNAME': 'USERNAME',
        'TRANSLATION_GUMMY_GATEWAY_UTOKYO_PASSWORD': 'PASSWORD',
        'TRANSLATION_GUMMY_SAMPLE': 'SAMPLE'}
        >>> write_environ(TRANSLATION_GUMMY_SAMPLE="SAMPLE_AMENDED")
        >>> read_environ()
        {'TRANSLATION_GUMMY_GATEWAY_UTOKYO_USERNAME': 'USERNAME',
        'TRANSLATION_GUMMY_GATEWAY_UTOKYO_PASSWORD': 'PASSWORD',
        'TRANSLATION_GUMMY_SAMPLE': 'SAMPLE_AMENDED'}
    """
    env_variables = read_environ(dotenv_path)
    env_variables.update(kwargs)
    with open(DOTENV_PATH, mode="w", encoding='utf-8') as f:
        f.writelines([f'{key} = "{val}"\n' for key,val in env_variables.items()])

def show_environ(dotenv_path=DOTENV_PATH):
    """Show environment variables written in ``dotenv_path``.

    Args:
        dotenv_path (str) : path/to/.env (default= ``DOTENV_PATH``)

    Examples:
        >>> from gummy.utils import show_environ
        >>> show_environ()
        * TRANSLATION_GUMMY_GATEWAY_UTOKYO_USERNAME : "USERNAME"
        * TRANSLATION_GUMMY_GATEWAY_UTOKYO_PASSWORD : "PASSWORD"    
    """
    env_variables = read_environ(dotenv_path=dotenv_path)
    for key,val in env_variables.items():
        print(f'* {toGREEN(key)} : "{toBLUE(val)}"')

def load_environ(dotenv_path=DOTENV_PATH, env_varnames=[], verbose=False):
    """
    Load environment variables from ``path`` file, and return whether every 
    necessary VARNAMES (``env_varnames``) are set. 

    Args:
        dotenv_path (str)   : path/to/.env (default= ``DOTENV_PATH``)
        env_varnames (list) : new environment variables
        verbose (bool)      : Whether to print message or not. (default= ``False``) 

    Returns:
        bool : Whether there are environment variables not defined in ``dotenv_path`` but in ``env_varnames``

    Examples:
        >>> from gummy.utils import load_environ, show_environ
        >>> is_ok = load_environ()
        >>> is_ok
        True
        >>> show_environ()
        * TRANSLATION_GUMMY_GATEWAY_UTOKYO_USERNAME : "USERNAME"
        * TRANSLATION_GUMMY_GATEWAY_UTOKYO_PASSWORD : "PASSWORD"
        >>> is_ok = load_environ(env_varnames=["TRANSLATION_GUMMY_NOT_DEFINED"])
        TRANSLATION_GUMMY_NOT_DEFINED is not set.
        EnvVariableNotDefinedWarning: Please set environment variable in /Users/iwasakishuto/.gummy/.env
        >>> is_ok
        False
    """
    if not os.path.exists(dotenv_path):
        return False
    load_dotenv(dotenv_path=dotenv_path, verbose=verbose)

    omission = False
    for env_name in env_varnames:
        if os.getenv(env_name) is None:
            omission = True
            print(f"{toGREEN(env_name)} is not set.")
    if omission:
        warnings.warn(message=f"Please set environment variable in {toBLUE(dotenv_path)}", category=EnvVariableNotDefinedWarning)
    return not omission

def check_environ(required_keynames, required_env_varnames=None, verbose=True, **kwargs):
    """Check whether meet the requirements.

    Args:
        required_keynames (list)     : Required keynames
        required_env_varnames (list) : Required environment variables.
        verbose (bool)               : Whether to print message or not. (default= ``True``) 

    Examples:
        >>> check_environ(
        ...     required_keynames=["hoge"],
        ...     required_env_varnames=["TRANSLATION_GUMMY_HOGE"],
        ...     hoge="hoge"
        >>> )
        (True, [])
        >>> check_environ(
        ...     required_keynames=["hoge"],
        ...     required_env_varnames=["TRANSLATION_GUMMY_HOGE"],
        ...     hoge1="hoge"
        >>> )
        Please set TRANSLATION_GUMMY_HOGE or give hoge as kwargs.
        (False, ['hoge'])

    Returns:
        tuple (bool, list) : 
            - ``is_ok`` : Whether meet the requirements.
            - ``not_meet_keynames`` : contains keynames you have to supply.
    """
    if required_env_varnames is None:
        required_env_varnames = [name2envname(name=keyname) for keyname in required_keynames]
    not_meet_keynames = []
    given_keynames = list(kwargs.keys())
    for keyname,env_name in zip(required_keynames, required_env_varnames):
        if (keyname not in given_keynames) and (os.getenv(env_name) is None):
            not_meet_keynames.append(keyname)
            if verbose: print(f"Please set {toGREEN(env_name)} or give {toBLUE(keyname)} as kwargs.")
    return len(not_meet_keynames)==0, not_meet_keynames
