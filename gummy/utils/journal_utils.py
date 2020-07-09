#coding: utf-8
import sys
import warnings
import requests
from bs4 import BeautifulSoup
from kerasy.utils import toRED, toBLUE, toGREEN, toACCENT

from ._warnings import JournalTypeIndistinguishableWarning

def canonicalize(url, driver=None):
    ret = requests.get(url=url)
    if not ret.ok:
        print(toRED(f"[{ret.status_code}] {ret.reason} : Failed to get {toBLUE(url)}"))
    cano_url = ret.url
    if cano_url != url:
        print(f"""Canonicalize url
        * From: {toBLUE(url)}
        * To  : {toBLUE(cano_url)}""")
    return cano_url

def whichJournal(url):
    """ Decide which journal from the twitter account at the URL. """
    # cano_url = canonicalize(url)
    twitter2jornal = {
        "@arxiv"      : "arXiv",
        "@nature"     : "Nature",
        "@naturenews" : "Nature"
    }
    soup = BeautifulSoup(requests.get(url).content, "html.parser")
    twitter_username = soup.find("meta", attrs={"name" : "twitter:site"}).get("content")
    journal_type = twitter2jornal.get(twitter_username)
    if journal_type is None:
        msg = f"{toGREEN(sys._getframe().f_code.co_name)} could not distinguish the journal type."
        warnings.warn(message=msg, category=JournalTypeIndistinguishableWarning)
    print(f"Estimated Journal Type : {toACCENT(journal_type)}")
    return journal_type