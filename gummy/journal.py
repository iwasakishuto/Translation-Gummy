# coding: utf-8
import re
import os
import time
import requests
from bs4 import BeautifulSoup
from kerasy.utils import toGREEN, toBLUE, toACCENT, handleKeyError
from pylatexenc.latex2text import LatexNodes2Text

from .utils import GUMMY_DIR
from .utils.gateway_utils import pass_gate_way
from .utils.environ_utils import load_environ, arrange_kwargs, popkwargs
from .utils.download_utils import download_file, decide_extension
from .utils.compress_utils import extract_from_compressed, is_compressed

def get_from_Nature(url, driver, need_gateway=True, sleep_for_loading=5, **kwargs):
    NatureDecomposeTags  = ["script", "style", "meta", "link", "noscript", "i", "sup"]
    NatureAvoidAriaLabel = ["Bib1", "author-information", "ethics", "additional-information", "rightslink", "article-info", "further-reading", "article-comments"]

    _ = load_environ()
    gateway_url_fmt = popkwargs(alias="gateway_url_format", default="{url}", kwargs=kwargs)
    if need_gateway:
        driver = pass_gate_way(
            driver = driver, 
            **arrange_kwargs(prefix_="TRANSLATION_GUMMY_GATEWAY_", except_alias_=["url_format"], **kwargs)
        )
    url = gateway_url_fmt.format(url=url)
    driver.get(url)
    print(f"Get {toBLUE(url)}\nNow loading...")
    time.sleep(sleep_for_loading)

    html = driver.page_source.encode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find(name="h1", attrs={"class" : "c-article-title"}).text
    for decoTag in soup(NatureDecomposeTags):
        decoTag.decompose()
    sections = soup.find_all("section")

    texts = []
    print("Contents of the paper")
    print("="*30)
    for section in sections:
        aria_labelledby = section.get("aria-labelledby")
        if aria_labelledby is None or aria_labelledby in NatureAvoidAriaLabel:
            continue
        h2Tag = section.find_all("h2")
        headline = h2Tag[0] if len(h2Tag)>0 else aria_labelledby
        text = section.get_text()
        if text.startswith(headline):
            text = text[len(headline):]
        print(f"{toGREEN(str(headline))} : {text[:10]}...")
        texts.append([headline, text])

    return title, texts

def get_from_arXiv(url, driver=None, need_gateway=False, **kwargs):
    arXivDecomposeTags  = ["<cit.>", "\xa0", "<ref>"]
    arXiv_no = url.split("/")[-1] # re.findall(pattern=r".*?\/?(\d+\.\d+)", string=url)[0]
    print(f"Get {toBLUE(url)}")
    soup = BeautifulSoup(requests.get(f"https://arxiv.org/abs/{arXiv_no}").content, "html.parser")
    title = soup.find("h1", attrs={"class" : "title mathjax"}).contents[1]
    print(f"Title: {toGREEN(title)}")

    path, _, ext = download_file(url=f"https://arxiv.org/e-print/{arXiv_no}", dirname=GUMMY_DIR)
    if is_compressed(ext):
        extracted_file_paths = extract_from_compressed(path, ext=".tex", dirname=GUMMY_DIR)
        path = extracted_file_paths[0]

    with open(path, mode="r") as ftex: 
        plain_text = LatexNodes2Text().latex_to_text(ftex.read())
    for decompose in arXivDecomposeTags:
        plain_text = plain_text.replace(decompose, "")
    plain_text = re.sub('[ 　]+', ' ', plain_text)
    sections = plain_text.replace("§.§", "§").split("§")

    texts = []
    print("Contents of the paper")
    print("="*30)
    for section in sections:
        first_nl = section.index("\n")
        headline = section[:first_nl].lstrip(" ").capitalize()
        text = section[first_nl:].replace("\n", "")
        print(f"{toGREEN(str(headline))} : {text[:10]}...")
        texts.append([headline, text])
    
    return title, texts

all = gummyJournalHandler = {
    "arxiv"  : get_from_arXiv, 
    "nature" : get_from_Nature,
}

twitter2jornal = {
    "@arxiv"  : "arXiv",
    "@nature" : "Nature",
    "@naturenews" : "Nature"
}

def whichJournal(url):
    """ Decide which journal from the twitter account at the URL. """
    soup = BeautifulSoup(requests.get(url).content, "html.parser")
    twitter_username = soup.find("meta", attrs={"name" : "twitter:site"}).get("content")
    handleKeyError(lst=twitter2jornal.keys(), twitter_username=twitter_username)
    return twitter2jornal.get(twitter_username)

def get(identifier):
    """
    Return a Translation-Gummy get_contents functions.
    @params identifier : string name or get_contents function.
    @return            : get_contents function.
    """
    if callable(identifier):
        return identifier
    elif isinstance(identifier, str):
        return gummyJournalHandler.get(identifier.lower())

def get_contents(url, driver, journal_type=None, need_gateway=True, **kwargs):
    if journal_type is None:
        journal_type = whichJournal(url)
        print(f"Estimated Journal Type : {toACCENT(journal_type)}")
    func = get(journal_type)
    title, texts = func(url=url, driver=driver, need_gateway=need_gateway, **kwargs)
    return title, texts