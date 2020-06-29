#coding: utf-8
import os
from dotenv import load_dotenv
from kerasy.utils import toBLUE, toGREEN

from . import ENV_PATH

TRANSLATION_ENV_NAMES = [
    "TRANSLATION_GUMMY_GATEWAY_URL",
    "TRANSLATION_GUMMY_GATEWAY_USERNAME",
    "TRANSLATION_GUMMY_GATEWAY_PASSWORD"
]

def load_environ(path=ENV_PATH):
    load_dotenv(dotenv_path=path)

    omission = False
    for env_name in TRANSLATION_ENV_NAMES:
        if os.getenv(env_name) is None:
            omission = True
            print(f"{toGREEN(env_name)} is not set.")
    if omission:
        print(f"Please set environment variable in {toBLUE(path)}")
    return omission

        