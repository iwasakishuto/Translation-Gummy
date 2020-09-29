#coding: utf-8
from .coloring_utils  import toBLUE, toGREEN

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
        print(
            "Could not create an instance of the Selenium WebDriver. If you want " + \
            "to check the error logs, please call " + toBLUE("gummy.utils.get_driver") + \
            " with specifying the " + toGREEN("driver_type") + " you want to look up." + \
            "If you can not prepare Selenium WebDriver by yourself, please build the environment using Docker." + \
            "Please see " + toBLUE("https://github.com/iwasakishuto/Translation-Gummy/tree/master/docker")
        )
