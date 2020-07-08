# coding: utf-8
import re
import os
import sys
import time
import requests
import warnings
from abc import ABCMeta
from bs4 import BeautifulSoup
from kerasy.utils import toGREEN, toBLUE, toRED, toACCENT, handleKeyError
from pylatexenc.latex2text import LatexNodes2Text

from .utils import GUMMY_DIR
from .utils import mk_class_get
from .utils.download_utils import download_file, decide_extension
from .utils.compress_utils import extract_from_compressed, is_compressed
from . import gateways

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
    handleKeyError(lst=twitter2jornal.keys(), twitter_username=twitter_username)
    journal_type = twitter2jornal.get(twitter_username)
    print(f"Estimated Journal Type : {toACCENT(journal_type)}")
    return journal_type

class GummyAbstJournal(metaclass=ABCMeta):
    """Abstract Jounal Crawlers
    If you want define your own journal crawlers, please inherit this class and define these methods:
    - crawl_type = "tex":
        - get_contents_soup(self, url, driver)
        - get_contents_tex(self, url, driver=None)
        - * get_contents_tex(self, url, driver=None)
        - * get_sections_from_tex(tex)
        - * get_texts_from_tex_sections(tex_sections)
    - crawl_type = "tex":
        - get_page_source(self, url, driver)
        - get_contents_tex(self, url, driver=None)
        - * get_contents_tex(self, url, driver=None)
        - * get_sections_from_tex(tex)
        - * get_texts_from_tex_sections(tex_sections)
    NOTE: Be sure to define the marked (*) functions.
    """
    def __init__(self, crawl_type="soup", gateway="useless", sleep_for_loading=3, DecomposeTags=[]):
        self.name  = self.__class__.__name__
        self.name_ = re.sub(r"([a-z])([A-Z])", r"\1_\2", self.name).lower()
        self.crawl_type = crawl_type.lower()
        self.gateway = gateways.get(gateway)
        self.sleep_for_loading = sleep_for_loading
        self.DecomposeTags = DecomposeTags

    def get_contents(self, url, driver=None, crawl_type=None):
        crawl_type = crawl_type or self.crawl_type
        CRAWL_TYPE_HANDLER = {
            "soup" : self.get_contents_soup,
            "tex"  : self.get_contents_tex,            
        }
        handleKeyError(lst=list(CRAWL_TYPE_HANDLER.keys()), crawl_type=crawl_type)
        func = CRAWL_TYPE_HANDLER.get(crawl_type)
        return func(url=url, driver=driver)

    # ================== #
    #  crawl_type="soup" #
    # ================== #

    def get_contents_soup(self, url, driver=None, **gatewaykwargs):
        """ Get contents from url using 'BeautifulSoup'.
        @params url    : (str)  page url
        @params driver : (WebDriver) webdriver
        @return title  : (str)  Title of paper
        @return texts  : (list) Each element is string tuple (headline, text).
        """
        cano_url = canonicalize(url=url, driver=driver)
        driver, fmt_url_func = self.gateway.passthrough(driver=driver, **gatewaykwargs)
        gateway_fmt_url = fmt_url_func(cano_url=cano_url)
        soup = self.get_page_source(url=gateway_fmt_url, driver=driver)
        title = self.get_title_from_soup(soup)
        soup_sections = self.get_sections_from_soup(soup)
        texts = self.get_texts_from_soup_sections(soup_sections)
        return (title, texts)
        
    def get_page_source(self, url, driver=None):
        """ Scrape and get page source from url.
        @params url    : (str) tex file url
        @params driver : (WebDriver) webdriver
        @return soup   : (BeautifulSoup)
        """
        print(f"Get {toBLUE(url)}")
        if driver is None:
            html = requests.get(url).content
        else:
            driver.get(url)
            for i in range(self.sleep_for_loading):
                sys.stdout.write(f"\rNow loading [{('#' * int(((i+1)/self.sleep_for_loading)/0.05)).ljust(20, '-')}]")
            print()
            html = driver.page_source.encode("utf-8")

        soup = BeautifulSoup(html, "html.parser")
        decoCounts = {tag:0 for tag in self.DecomposeTags+[None]}
        for decoTag in soup.find_all(name=self.DecomposeTags):
            decoCounts[decoTag.name] += 1
            decoTag.decompose()
        for decoTag, count in decoCounts.items():
            print(f"Decomposed {toGREEN(f'<{decoTag}>')} tag ({count})")
        return soup

    def get_title_from_soup(self, soup):
        """ Get page title from page source.
        @params soup     : (BeautifulSoup)
        @return title    : (str) page title
        """
        title = soup.find("title")
        return title

    def get_sections_from_soup(self, soup):
        """ Get sections from page source.
        @params soup     : (BeautifulSoup)
        @return sections : (list) Each element is (bs4.element.Tag)
        """
        sections = soup.find_all("section")
        return sections

    def get_texts_from_soup_sections(self, soup_sections):
        """ Get text for each soup section.
        @params soup_sections : (list) Each element is (bs4.element.Tag)
        @return texts         : (list) Each element is string tuple (headline, text).
        """
        texts = []
        print("Contents of the paper")
        print("="*30)
        # for section in soup_sections:
        #     headline = get_headline(section)
        #     text = section.get_text()
        #     print(f"{toGREEN(str(headline))} : {text.split(' ')[:3]}...")
        #     texts.append([headline, text])
        return texts

    # ================== #
    #  crawl_type="tex"  #
    # ================== #

    def get_contents_tex(self, url, driver=None):
        """ Get contents from url by parsing TeX sources.
        @params url    : (str)  page url
        @params driver : (WebDriver) webdriver
        @return title  : (str)  Title of paper
        @return texts  : (list) Each element is string tuple (headline, text).
        """
        tex = self.get_tex_source(url=url, driver=driver)
        title = self.get_title_from_tex(tex)
        tex_sections = self.get_sections_from_tex(tex)
        texts = self.get_texts_from_tex_sections(tex_sections)
        return (title, texts)

    def get_tex_source(self, url, driver=None):
        """ Download and get tex source from url.
        @params url    : (str) tex file url
        @params driver : (WebDriver) webdriver
        @return tex    : (str) Plain text of tex sources.
        """
        path, _, ext = download_file(url=url, dirname=GUMMY_DIR)
        if is_compressed(ext):
            extracted_file_paths = extract_from_compressed(path, ext=".tex", dirname=GUMMY_DIR)
            path = extracted_file_paths[0]

        with open(path, mode="r") as ftex: 
            tex = LatexNodes2Text().latex_to_text(ftex.read())
        for decompose in self.DecomposeTags:
            tex = tex.replace(decompose, "")
        tex = re.sub('[ 　]+', ' ', tex)
        return tex

    def get_title_from_tex(self, tex):
        """ Get page title from tex source.
        @params tex   : (str) Plain text of tex sources.
        @return title : (str) page title
        """
        title = "title"
        return title

    def get_sections_from_tex(self, tex):
        """ Get sections from tex source.
        @params tex      : (str) Plain text of tex sources.
        @return sections : (list) Each element is plain text (str)
        """
        sections = ["sections"]
        return sections    

    def get_texts_from_tex_sections(self, tex_sections):
        """ Get text for each tex section.
        @params soup_sections : (list) Each element is plain text (str)
        @return texts         : (list) Each element is string tuple (headline, text).
        """
        texts = []
        print("Contents of the paper")
        print("="*30)
        # for section in tex_sections:
        #     first_nl = section.index("\n")
        #     headline = section[:first_nl].lstrip(" ").capitalize()
        #     text = section[first_nl:].replace("\n", "")
        #     print(f"{toGREEN(str(headline))} : {text.split(' ')[:3]}...")
        #     texts.append([headline, text])
        return texts

class NatureCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            DecomposeTags=['i', 'link', 'meta', 'noscript', 'script', 'style', 'sup'],
        )
        self.AvoidAriaLabel = [None, 'Bib1', 'additional-information', 'article-comments', 'article-info', 'author-information', 'ethics', 'further-reading', 'rightslink']

    def get_title_from_soup(self, soup):
        title = soup.find(name="h1", attrs={"class" : "c-article-title"}).text
        return title

    def get_sections_from_soup(self, soup):
        sections = [e for e in soup.find_all("section") if e.get("aria-labelledby") not in self.AvoidAriaLabel]
        return sections

    def get_texts_from_soup_sections(self, soup_sections):
        texts = super().get_texts_from_soup_sections(soup_sections)
        for section in soup_sections:
            aria_labelledby = section.get("aria-labelledby")
            h2Tag = section.find_all("h2")
            headline = h2Tag[0] if len(h2Tag)>0 else aria_labelledby
            text = section.get_text()
            print(f"{toGREEN(str(headline))} : {text.split(' ')[:3]}...")
            texts.append([headline, text])
        return texts

class arXivCrawler(GummyAbstJournal):
    def __init__(self, sleep_for_loading=3, **kwargs):
        super().__init__(
            crawl_type="tex", 
            gateway="useless",
            sleep_for_loading=sleep_for_loading,
            DecomposeTags=["<cit.>", "\xa0", "<ref>"],
        )
        self.AvoidAriaLabel = [None, 'Bib1', 'additional-information', 'article-comments', 'article-info', 'author-information', 'ethics', 'further-reading', 'rightslink']

    def get_contents_tex(self, url, driver=None):
        """ Get contents from url by parsing TeX sources.
        @params url    : (str)  page url
        @params driver : (WebDriver) webdriver
        @return title  : (str)  Title of paper
        @return texts  : (list) Each element is string tuple (headline, text).
        """
        arXiv_no = url.split("/")[-1] # re.findall(pattern=r".*?\/?(\d+\.\d+)", string=url)[0]
        tex = self.get_tex_source(url=f"https://arxiv.org/e-print/{arXiv_no}", driver=None)
        # title = self.get_title_from_tex(tex)
        soup = self.get_page_source(url=f"https://arxiv.org/abs/{arXiv_no}", driver=None)
        title = self.get_title_from_soup(soup)
        tex_sections = self.get_sections_from_tex(tex)
        texts = self.get_texts_from_tex_sections(tex_sections)
        return (title, texts)
        
    def get_title_from_tex(self, tex):
        raise NotImplementedError("Not Impremented.")

    def get_sections_from_tex(self, tex):
        sections = tex.replace("§.§", "§").split("§")
        return sections   
    
    def get_texts_from_tex_sections(self, tex_sections):
        texts = super().get_texts_from_soup_sections(tex_sections)
        for section in tex_sections:
            first_nl = section.index("\n")
            headline = section[:first_nl].lstrip(" ").capitalize()
            text = section[first_nl:].replace("\n", "")
            print(f"{toGREEN(str(headline))} : {text[:10]}...")
            texts.append([headline, text])
        return texts

    def get_title_from_soup(self, soup):
        """ Get page title from page source.
        @params soup     : (BeautifulSoup)
        @return title    : (str) page title
        """
        title = soup.find("h1", attrs={"class" : "title mathjax"}).contents[1]
        return title

all = TranslationGummyJournalCrawlers = {
    "arxiv"  : arXivCrawler, 
    "nature" : NatureCrawler,
}

get = mk_class_get(
    all_classes=TranslationGummyJournalCrawlers,
    gummy_abst_class=[GummyAbstJournal],
    genre="journals"
)

