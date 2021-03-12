#coding: utf-8
from .coloring_utils  import toBLUE, toGREEN, toRED

__all__ = [
    "GummyImprementationWarning", 
    "EnvVariableNotDefinedWarning",
    "DriverNotFoundWarning",
]

class GummyImprementationWarning(Warning):
    """ 
    Warnings that developers will resolve. 
    Developers are now solving in a simple stupid way.
    """

class EnvVariableNotDefinedWarning(Warning):
    """
    Warnings when necessary environment variables are not defined. Use ``write_environ``
    function to define them.

    Examples:

        >>> from gummy.utils import write_environ
        >>> write_environ(
        ...     TRANSLATION_GUMMY_GATEWAY_UTOKYO_USERNAME="username",
        ...     TRANSLATION_GUMMY_GATEWAY_UTOKYO_PASSWORD="password",
        >>> )
    """

class DriverNotFoundWarning(Warning):
    """
    Warnings when launching all supported drivers fails.
    """
    def __init__(self, message):
        super().__init__(message)
        print(f"""
+---------------- {toRED("Driver Not Found Warning")} ----------------+
| Could not create an instance of the Selenium WebDriver.  |
| If you want to check the error logs, please run the      |
| following command.                                       |
|                                                          |
| $ python                                                 |
| >>> from gummy.utils import get_driver                   |
| >>> # chose driver_type you want to look up.             |
| >>> get_driver(driver_type="local")                      |
|                                                          |
| +--- {toGREEN("[Error Handling]")} ---------------------------------+ |
| |{toRED("SessionNotCreatedException")}                            | |
| | This error is due to the non-correspondence between  | |
| | ChromeDriver and Chrome (Browser). Each version of   | |
| | ChromeDriver only supports Chrome with matching      | |
| | major, minor, and build version numbers, so please   | |
| | visit {toBLUE("https://chromedriver.chromium.org/downloads")}    | |
| | and download ChromeDriver matching your Chrome       | |
| | version. (You can check your Chrome version by       | |
| | accessing {toBLUE("chrome://settings/help")})                    | |
| +------------------------------------------------------+ |
|                                                          |
| If you can not prepare Selenium WebDriver by yourself,   |
| please build the environment using Docker. (Dockerfile   |
| is at Github Repository. See                             |
| {toBLUE("https://github.com/iwasakishuto/Translation-Gummy")}        |
+----------------------------------------------------------+
""")