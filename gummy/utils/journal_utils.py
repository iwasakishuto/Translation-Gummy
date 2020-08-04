#coding: utf-8
import os
import re
import sys
import time
import warnings
import requests
import webbrowser
from bs4 import BeautifulSoup

from ._exceptions import JournalTypeIndistinguishableError
from .coloring_utils import toRED, toBLUE, toGREEN, toACCENT

DOMAIN2JOURNAL = {
    "academic.oup.com"                          : "OxfordAcademic",
    "advances.sciencemag.org"                   : "ScienceAdvances",
    "arxiv.org"                                 : "arXiv",
    "bio.biologists.org"                        : "Biologists",
    "bmcbioinformatics.biomedcentral.com"       : "BMC",
    "dev.biologists.org"                        : "Biologists",
    "febs.onlinelibrary.wiley.com"              : "FEBS",
    "ieeexplore.ieee.org"                       : "ieee",
    "jcs.biologists.org"                        : "Biologists",
    "journals.plos.org"                         : "PLOSONE",
    "keio.pure.elsevier.com"                    : "UniKeio",
    "link.springer.com"                         : "Springer",
    "linkinghub.elsevier.com"                   : "ScienceDirect",
    "onlinelibrary.wiley.com"                   : "Wiley",
    "pubmed.ncbi.nlm.nih.gov"                   : "PubMed",
    "pubs.acs.org"                              : "ACS",
    "pubs.rsc.org"                              : "RSC",
    "retrovirology.biomedcentral.com"           : "BMC",
    "rnajournal.cshlp.org"                      : "RNAjournal",
    "stemcellsjournals.onlinelibrary.wiley.com" : "StemCells",
    "www.aclweb.org"                            : "ACLAnthology",
    "www.biorxiv.org"                           : "bioRxiv",
    "www.cell.com"                              : "CellPress",
    "www.frontiersin.org"                       : "frontiers",
    "www.intechopen.com"                        : "IntechOpen",
    "www.jbc.org"                               : "JBC",
    "www.jsse.org"                              : "JSSE",
    "www.jstage.jst.go.jp"                      : "JSTAGE",
    "www.lungcancerjournal.info"                : "LungCancer",
    "www.medrxiv.org"                           : "medRxiv",
    "www.mdpi.com"                              : "MDPI",
    "www.nature.com"                            : "Nature",
    "www.ncbi.nlm.nih.gov"                      : "NCBI",
    "www.nrcresearchpress.com"                  : "NRCResearchPress",
    "www.ou.edu"                                : "UniOKLAHOMA",
    "www.pnas.org"                              : "PNAS",
    "www.sciencedirect.com"                     : "ScienceDirect",
    "www.spandidos-publications.com"            : "Spandidos",
    "www.tandfonline.com"                       : "TandFOnline",
}

def canonicalize(url, driver=None, sleep_for_loading=1):
    if driver is not None:
        driver.get(url)
        time.sleep(sleep_for_loading)
        cano_url = driver.current_url
    else:
        try:
            ret = requests.get(url=url)
            cano_url = ret.url
        except:
            cano_url = url
    return cano_url

def whichJournal(url, driver=None, verbose=True):
    """ Decide which journal from the twitter account at the URL. """
    ext = os.path.splitext(url)[-1]
    if ext == ".pdf":
        journal_type = "pdf"
    else:
        url = canonicalize(url, driver=driver)
        url_domain = re.match(pattern=r"^https?:\/\/(.+?)\/", string=url).group(1)
        journal_type = DOMAIN2JOURNAL.get(url_domain)
        if journal_type is None:
            webbrowser.open(f"https://www.twitter.com/messages/compose?recipient_id=1042783905697288193&text=Please%20support%20this%20journal%3A%20{url}")
            msg = f"""
            {toGREEN('gummy.utils.journal_utils.whichJournal')} could not distinguish the journal type.
            * Please send a DM to the developer to support this journal ({toBLUE(url)})
            * Please specify the {toBLUE('journal_type')} explicitly until it is supported.
            * {toRED('I would really appreciate it if you could send a pull request.')}
            """
            raise JournalTypeIndistinguishableError(msg)
    if verbose: print(f"Estimated Journal Type : {toACCENT(journal_type)}")
    return journal_type.lower()