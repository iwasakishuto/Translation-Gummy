#coding: utf-8
import re
import sys
import warnings
import requests
import webbrowser
from bs4 import BeautifulSoup
from kerasy.utils import toRED, toBLUE, toGREEN, toACCENT

from ._exceptions import JournalTypeIndistinguishableError

def canonicalize(url, driver=None):
    ret = requests.get(url=url)
    if ret.ok:
        cano_url = ret.url
    else:
        print(toRED(f"[{ret.status_code}] {ret.reason} : Failed to get {toBLUE(url)} by {toGREEN('requests')} library."))
        if driver is not None:
            driver.get(url)
            cano_url = driver.current_url
        else:
            cano_url = ret.url
    return cano_url

def whichJournal(url):
    """ Decide which journal from the twitter account at the URL. """
    url = canonicalize(url)
    prefix2jornal = [
        ("arxiv.org", "arXiv"),
        ("www.nature.com/", "Nature"),
        ("www.ncbi.nlm.nih.gov/pmc/", "PubMed"),
    ]
    match = re.match(pattern=r"^https?://(.+)$", string=url)
    try:
        journal_type = [journal for (prefix,journal) in prefix2jornal if match.group(1).startswith(prefix)][0]
        print(f"Estimated Journal Type : {toACCENT(journal_type)}")
    except (AttributeError, IndexError):
        webbrowser.open(f"https://www.twitter.com/messages/compose?recipient_id=1042783905697288193&text=Please%20support%20this%20journal%3A%20{url}")
        msg = f"""
        {toGREEN('gummy.utils.journal_utils.whichJournal')} could not distinguish the journal type.
        * Please send a DM to the developer to support this journal ({toBLUE(url)})
        * Please specify the {toBLUE('journal_type')} explicitly until it is supported.
        * {toRED('I would really appreciate it if you could send a pull request.')}
        """
        raise JournalTypeIndistinguishableError(msg)
    return journal_type.lower()