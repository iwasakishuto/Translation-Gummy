#coding: utf-8

__all__ = ["GummyImprementationWarning", "EnvVariableNotDefinedWarning"]

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