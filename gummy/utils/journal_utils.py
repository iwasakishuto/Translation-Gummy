#coding: utf-8
""" Utility programs for :mod:`journals <gummy.journals>` """
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
    "agupubs.onlinelibrary.wiley.com"           : "AGUPublications",
    "ajp.amjpathol.org"                         : "ASIP",
    "anatomypubs.onlinelibrary.wiley.com"       : "AnatomyPubs",
    "arxiv.org"                                 : "arXiv",
    "bio.biologists.org"                        : "Biologists",
    "biologydirect.biomedcentral.com"           : "BioMedCentral",
    "biomedgrid.com"                            : "BiomedGrid",
    "bmcbioinformatics.biomedcentral.com"       : "BioMedCentral",
    "bmcevolbiol.biomedcentral.com"             : "BioMedCentral",
    "bmcgenomics.biomedcentral.com"             : "BioMedCentral",
    "bmcmedicine.biomedcentral.com"             : "BioMedCentral",
    "dev.biologists.org"                        : "Biologists",
    "dl.acm.org"                                : "ACM",
    "eymj.org"                                  : "YMJ",
    "febs.onlinelibrary.wiley.com"              : "WileyOnlineLibrary",
    "genesdev.cshlp.org"                        : "GeneDev",
    "ieeexplore.ieee.org"                       : "ieeexplore",
    "iovs.arvojournals.org"                     : "ARVOJournals",
    "jamanetwork.com"                           : "JAMANetwork",
    "jcs.biologists.org"                        : "Biologists",
    "jkms.org"                                  : "JKMS",
    "journals.ametsoc.org"                      : "AMS",
    "journals.aps.org"                          : "APS",
    "journals.lww.com"                          : "LWWJournals",
    "journals.physiology.org"                   : "RenalPhysiology",
    "journals.plos.org"                         : "PLOSONE",
    "journals.sagepub.com"                      : "SAGEjournals",
    "jov.arvojournals.org"                      : "ARVOJournals",
    "keio.pure.elsevier.com"                    : "UniKeio",
    "learnmem.cshlp.org"                        : "LearningMemory",
    "link.springer.com"                         : "Springer",
    "linkinghub.elsevier.com"                   : "ScienceDirect",
    "mcb.asm.org"                               : "MolCellBio",
    "onlinelibrary.wiley.com"                   : "WileyOnlineLibrary",
    "pubmed.ncbi.nlm.nih.gov"                   : "PubMed",
    "pubs.acs.org"                              : "ACSPublications",
    "pubs.rsc.org"                              : "RSCPublishing",
    "pubs.rsna.org"                             : "RadioGraphics",
    "retrovirology.biomedcentral.com"           : "BioMedCentral",
    "rnajournal.cshlp.org"                      : "RNAjournal",
    "science.sciencemag.org"                    : "ScienceMag",
    "stemcellsjournals.onlinelibrary.wiley.com" : "StemCells",
    "tvst.arvojournals.org"                     : "ARVOJournals",
    "www.aclweb.org"                            : "ACLAnthology",
    "www.biorxiv.org"                           : "bioRxiv",
    "www.bioscience.org"                        : "Bioscience",
    "www.cell.com"                              : "CellPress",
    "www.e-ce.org"                              : "ClinicalEndoscopy",
    "www.embopress.org"                         : "EMBOPress",
    "www.genetics.org"                          : "Genetics",
    "www.frontiersin.org"                       : "frontiers",
    "www.future-science.com"                    : "FutureScience",
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
    "www.nejm.org"                              : "NEJM",
    "www.nrcresearchpress.com"                  : "NRCResearchPress",
    "www.nrronline.org"                         : "NRR",
    "www.oncotarget.com"                        : "Oncotarget",
    "www.ou.edu"                                : "UniOKLAHOMA",
    "www.plantphysiol.org"                      : "ASPB",
    "www.pnas.org"                              : "PNAS",
    "www.psychiatrist.com"                      : "PsyChiArtist",
    "www.sciencedirect.com"                     : "ScienceDirect",
    "www.spandidos-publications.com"            : "Spandidos",
    "www.tandfonline.com"                       : "TaylorandFrancisOnline",
    "www.thelancet.com"                         : "TheLancet",
}

def canonicalize(url, driver=None, sleep_for_loading=1):
    """canonicalize the URL by accessing the URL once.

    Args:
        url (str)               : URL of the paper.
        driver (WebDriver)      : Selenium WebDriver. (default= ``None``)
        sleep_for_loading (int) : Number of seconds to wait for a web page to load (default= ``1`` )
    
    Returns:
        str : canonized URL.
    """

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
    """ Decide which journal from the domain of the ``url``

    If the ``journal_type`` cannot be determined, Twitter DM |twitter badge| will 
    open automatically, so please feel free to request it to the developer.

    Args:
        url (str)          : URL of the paper.
        driver (WebDriver) : Selenium WebDriver. (default= ``None``)
        verbose (bool)     : Whether to print message or not. (default= ``True``) 

    Returns:
        str : journal_type

    Examples:
        >>> journal_type = whichJournal("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1573881/")
        Estimated Journal Type : NCBI
        >>> journal_type
        'ncbi'

    .. |twitter badge| image:: https://img.shields.io/badge/twitter-Requests-1da1f2?style=flat-square&logo=twitter
        :target: https://www.twitter.com/messages/compose?recipient_id=1042783905697288193&text=Please%20support%20this%20journal%3A%20
    """
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