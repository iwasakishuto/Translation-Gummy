# coding: utf-8
""" Utility programs for coloring output. """

__all__ = [
    "toGRAY", "toRED", "toGREEN", "toYELLOW", "toBLUE", "toPURPLE", "toCYAN",
    "toWHITE", "toREVERSE", "toACCENT", "toFLASH", "toRED_FLASH",
]

def _toCOLOR_create(color):
    color = color.upper()
    charcode = {
        "BLACK"     : "",
        "GRAY"      : "\033[30m",
        "RED"       : "\033[31m",
        "GREEN"     : "\033[32m",
        "YELLOW"    : "\033[33m",
        "BLUE"      : "\033[34m",
        "PURPLE"    : "\033[35m",
        "CYAN"      : "\033[36m",
        "WHITE"     : "\033[37m",
        "REVERSE"   : "\033[07m",
        "ACCENT"    : "\033[01m",
        "FLASH"     : "\033[05m",
        "RED_FLASH" : "\033[05;41m",
        "END"       : "\033[0m",
    }.get(color, "\033[34m")
    func = lambda x: f"{charcode}{str(x)}\033[0m"
    func.__doc__ = f"""Convert the output color to {color}
    
    Args:
        x (str): string
        
    Examples:
        >>> from gummy.utils import to{color}
        >>> print(to{color}("hoge"))
        hoge
    """
    return func

toGRAY      = _toCOLOR_create(color="GRAY")
toRED       = _toCOLOR_create(color="RED")
toGREEN     = _toCOLOR_create(color="GREEN")
toYELLOW    = _toCOLOR_create(color="YELLOW")
toBLUE      = _toCOLOR_create(color="BLUE")
toPURPLE    = _toCOLOR_create(color="PURPLE")
toCYAN      = _toCOLOR_create(color="CYAN")
toWHITE     = _toCOLOR_create(color="WHITE")
toREVERSE   = _toCOLOR_create(color="REVERSE")
toACCENT    = _toCOLOR_create(color="ACCENT")
toFLASH     = _toCOLOR_create(color="FLASH")
toRED_FLASH = _toCOLOR_create(color="RED_FLASH")