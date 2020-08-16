#coding: utf-8
import os
import re
import sys
import time
import warnings
import requests
from bs4 import BeautifulSoup

from ._exceptions import JournalTypeIndistinguishableError
from .coloring_utils import toRED, toBLUE, toGREEN, toACCENT

DOMAIN2JOURNAL = {
    "academic.oup.com"                          : "OxfordAcademic",
    "advances.sciencemag.org"                   : "ScienceAdvances",
    "ajp.amjpathol.org"                         : "ASIP",
    "anatomypubs.onlinelibrary.wiley.com"       : "AnatomyPubs",
    "arxiv.org"                                 : "arXiv",
    "bio.biologists.org"                        : "Biologists",
    "biologydirect.biomedcentral.com"           : "BioMedCentral",
    "bmcbioinformatics.biomedcentral.com"       : "BioMedCentral",
    "bmcevolbiol.biomedcentral.com"             : "BioMedCentral",
    "bmcgenomics.biomedcentral.com"             : "BioMedCentral",
    "dev.biologists.org"                        : "Biologists",
    "dl.acm.org"                                : "ACM",
    "febs.onlinelibrary.wiley.com"              : "FEBS",
    "genesdev.cshlp.org"                        : "GeneDev",
    "ieeexplore.ieee.org"                       : "ieee",
    "jamanetwork.com"                           : "JAMANetwork",
    "jcs.biologists.org"                        : "Biologists",
    "jkms.org"                                  : "JKMS",
    "journals.ametsoc.org"                      : "AMS",
    "journals.aps.org"                          : "APS",
    "journals.physiology.org"                   : "RenalPhysiology",
    "journals.plos.org"                         : "PLOSONE",
    "journals.sagepub.com"                      : "SAGEjournals",
    "keio.pure.elsevier.com"                    : "UniKeio",
    "link.springer.com"                         : "Springer",
    "linkinghub.elsevier.com"                   : "ScienceDirect",
    "mcb.asm.org"                               : "MolCellBio",
    "onlinelibrary.wiley.com"                   : "Wiley",
    "pubmed.ncbi.nlm.nih.gov"                   : "PubMed",
    "pubs.acs.org"                              : "ACS",
    "pubs.rsc.org"                              : "RSC",
    "pubs.rsna.org"                             : "RadioGraphics",
    "retrovirology.biomedcentral.com"           : "BioMedCentral",
    "rnajournal.cshlp.org"                      : "RNAjournal",
    "stemcellsjournals.onlinelibrary.wiley.com" : "StemCells",
    "www.aclweb.org"                            : "ACLAnthology",
    "www.biorxiv.org"                           : "bioRxiv",
    "www.bioscience.org"                        : "Bioscience",
    "www.cell.com"                              : "CellPress",
    "www.genetics.org"                          : "Genetics",
    "www.frontiersin.org"                       : "frontiers",
    "www.intechopen.com"                        : "IntechOpen",
    "www.jbc.org"                               : "JBC",
    "www.jkms.org"                              : "JKMS",
    "www.jkns.or.kr"                            : "JKNS",
    "www.jpedsurg.org"                          : "PediatricSurgery",
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
    url = canonicalize(url, driver=driver)
    if url.startswith("data:"):
        journal_type = "pdf"
    else:
        url_domain = re.match(pattern=r"^https?:\/\/(.+?)\/", string=url).group(1)
        journal_type = DOMAIN2JOURNAL.get(url_domain)
        if journal_type is None:
            if ext == ".pdf":
                journal_type = "pdf"
            else:
                msg = f"""
                {toGREEN('gummy.utils.journal_utils.whichJournal')} could not distinguish the journal type.
                * Please send a DM to the developer to support this journal ({toBLUE(url)})
                * Please specify the {toBLUE('journal_type')} explicitly until it is supported.
                * {toRED('I would really appreciate it if you could send a pull request.')}
                """
                raise JournalTypeIndistinguishableError(msg=msg, url=url)
    if verbose: print(f"Estimated Journal Type : {toACCENT(journal_type)}")
    return journal_type.lower()