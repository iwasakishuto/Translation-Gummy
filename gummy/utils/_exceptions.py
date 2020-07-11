#coding: utf-8

__all__ = ["GummyImprementationError", "JournalTypeIndistinguishableError"]

class GummyImprementationError(Exception):
    """ 
    Warnings that developers will resolve. 
    Developers are now solving in a simple stupid way.
    """

class JournalTypeIndistinguishableError(Exception):
    """
    Warnings when Translation-Gummy could not distinguish the journal type.
    """