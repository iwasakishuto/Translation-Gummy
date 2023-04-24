# coding: utf-8
""" Utility programs for coloring output. """

from typing import Callable, Dict, Literal

from ._type import T_Color2code, T_ColorNames

__all__ = [
    "toGRAY",
    "toRED",
    "toGREEN",
    "toYELLOW",
    "toBLUE",
    "toPURPLE",
    "toCYAN",
    "toWHITE",
    "toREVERSE",
    "toACCENT",
    "toFLASH",
    "toRED_FLASH",
]


def _toCOLOR_create(color: T_ColorNames) -> Callable[[object], str]:
    name2code: T_Color2code = {
        "BLACK": "",
        "GRAY": "\033[30m",
        "RED": "\033[31m",
        "GREEN": "\033[32m",
        "YELLOW": "\033[33m",
        "BLUE": "\033[34m",
        "PURPLE": "\033[35m",
        "CYAN": "\033[36m",
        "WHITE": "\033[37m",
        "REVERSE": "\033[07m",
        "ACCENT": "\033[01m",
        "FLASH": "\033[05m",
        "RED_FLASH": "\033[05;41m",
        "END": "\033[0m",
    }
    charcode: str = name2code.get(color, "\033[34m")
    func: Callable[[object], str] = lambda x: f"{charcode}{str(x)}\033[0m"
    func.__doc__ = f"""Convert the output color to {color}

    Args:
        x (str): string

    Examples:
        >>> from gummy.utils import to{color}
        >>> print(to{color}("hoge"))
        hoge
    """
    return func


toGRAY: Callable[[object], str] = _toCOLOR_create(color="GRAY")
toRED: Callable[[object], str] = _toCOLOR_create(color="RED")
toGREEN: Callable[[object], str] = _toCOLOR_create(color="GREEN")
toYELLOW: Callable[[object], str] = _toCOLOR_create(color="YELLOW")
toBLUE: Callable[[object], str] = _toCOLOR_create(color="BLUE")
toPURPLE: Callable[[object], str] = _toCOLOR_create(color="PURPLE")
toCYAN: Callable[[object], str] = _toCOLOR_create(color="CYAN")
toWHITE: Callable[[object], str] = _toCOLOR_create(color="WHITE")
toREVERSE: Callable[[object], str] = _toCOLOR_create(color="REVERSE")
toACCENT: Callable[[object], str] = _toCOLOR_create(color="ACCENT")
toFLASH: Callable[[object], str] = _toCOLOR_create(color="FLASH")
toRED_FLASH: Callable[[object], str] = _toCOLOR_create(color="RED_FLASH")
