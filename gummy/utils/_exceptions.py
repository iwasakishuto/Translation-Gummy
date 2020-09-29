#coding: utf-8
import webbrowser

__all__ = [
    "GummyImprementationError", 
    "JournalTypeIndistinguishableError"
]

class GummyImprementationError(Exception):
    """ 
    Warnings that developers will resolve. 
    Developers are now solving in a simple stupid way.
    """

class JournalTypeIndistinguishableError(Exception):
    """
    Warnings when Translation-Gummy could not distinguish the journal type.
    """
    def __init__(self, msg, url=None):
        super().__init__(msg)
        if url is not None:
            webbrowser.open(f"https://www.twitter.com/messages/compose?recipient_id=1042783905697288193&text=Please%20support%20this%20journal%3A%20{url}")

class KeyError(KeyError):
    def __str__(self):
        return ', '.join(self.args)