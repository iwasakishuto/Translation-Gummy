# coding: utf-8

__all__ = [
    "toRED", "toGREEN", "toYELLOW", "toBLUE", "toPURPLE", "toCYAN",
    "toWHITE", "toRETURN", "toACCENT", "toFLASH", "toRED_FLASH",
]

def make_2COLOR_funcs(color="BLUE"):
    code = {
        "BLACK"     : '\033[30m',
        "RED"       : '\033[31m',
        "GREEN"     : '\033[32m',
        "YELLOW"    : '\033[33m',
        "BLUE"      : '\033[34m',
        "PURPLE"    : '\033[35m',
        "CYAN"      : '\033[36m',
        "WHITE"     : '\033[37m',
        "RETURN"    : '\033[07m',
        "ACCENT"    : '\033[01m',
        "FLASH"     : '\033[05m',
        "RED_FLASH" : '\033[05;41m',
        "END"       : '\033[0m',
    }.get(color.upper())
    func = lambda x: f"{code}{x}\033[0m"
    return func

toRED       = make_2COLOR_funcs("RED")
toGREEN     = make_2COLOR_funcs("GREEN")
toYELLOW    = make_2COLOR_funcs("YELLOW")
toBLUE      = make_2COLOR_funcs("BLUE")
toPURPLE    = make_2COLOR_funcs("PURPLE")
toCYAN      = make_2COLOR_funcs("CYAN")
toWHITE     = make_2COLOR_funcs("WHITE")
toRETURN    = make_2COLOR_funcs("RETURN")
toACCENT    = make_2COLOR_funcs("ACCENT")
toFLASH     = make_2COLOR_funcs("FLASH")
toRED_FLASH = make_2COLOR_funcs("RED_FLASH")