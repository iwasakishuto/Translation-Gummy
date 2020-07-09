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

from . import gateways
from .utils._path import GUMMY_DIR
from .utils.compress_utils import extract_from_compressed, is_compressed
from .utils.download_utils import download_file, decide_extension, src2base64
from .utils.generic_utils import mk_class_get
from .utils.journal_utils import canonicalize, whichJournal
from .utils.soup_utils import split_soup

class GummyAbstJournal(metaclass=ABCMeta):
    """Abstract Jounal Crawlers
    If you want define your own journal crawlers, please inherit this class and define these methods:
    - crawl_type = "tex":
        - get_contents_soup(self, url, driver)
        - get_contents_tex(self, url, driver=None)
        - * get_contents_tex(self, url, driver=None)
        - * get_sections_from_tex(tex)
        - * get_contents_from_tex_sections(tex_sections)
    - crawl_type = "tex":
        - get_soup_source(self, url, driver)
        - get_contents_tex(self, url, driver=None)
        - * get_contents_tex(self, url, driver=None)
        - * get_sections_from_tex(tex)
        - * get_contents_from_tex_sections(tex_sections)
    NOTE: Be sure to define the marked (*) functions.
    """
    def __init__(self, crawl_type="soup", gateway="useless", sleep_for_loading=3, 
                 DecomposeTexTags=["<cit.>", "\xa0", "<ref>"], 
                 DecomposeSoupTags=['i','link','meta','noscript','script','style','sup']):
        self.name  = self.__class__.__name__
        self.name_ = re.sub(r"([a-z])([A-Z])", r"\1_\2", self.name).lower()
        self.crawl_type = crawl_type.lower()
        self.gateway = gateways.get(gateway)
        self.sleep_for_loading = sleep_for_loading
        self.DecomposeTexTags = DecomposeTexTags
        self.DecomposeSoupTags = DecomposeSoupTags

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

    def get_contents_soup(self, url, journal_type=None, driver=None, **gatewaykwargs):
        """ Get contents from url using 'BeautifulSoup'.
        @params url      : (str)  page url
        @params driver   : (WebDriver) webdriver
        @return title    : (str)  Title of paper
        @return contents : (list) Each element is dict (key is `en`, `img`, or `headline`).
        """
        soup = self.get_soup_source(url=url, journal_type=journal_type, driver=driver, **gatewaykwargs)
        title = self.get_title_from_soup(soup)
        soup_sections = self.get_sections_from_soup(soup)
        contents = self.get_contents_from_soup_sections(soup_sections)
        return (title, contents)
        
    def get_soup_source(self, url, journal_type=None, driver=None, **gatewaykwargs):
        """ Scrape and get page source from url.
        @params url    : (str) tex file url
        @params driver : (WebDriver) webdriver
        @return soup   : (BeautifulSoup)
        """
        cano_url = canonicalize(url=url, driver=driver)
        driver, fmt_url_func = self.gateway.passthrough(driver=driver, url=cano_url, journal_type=journal_type, **gatewaykwargs)
        gateway_fmt_url = fmt_url_func(cano_url=cano_url)
        if driver is None:
            html = requests.get(url=url).content
            print(f"Get {toBLUE(url)}")
        else:
            driver.get(gateway_fmt_url)
            print(f"Get {toBLUE(gateway_fmt_url)}")
            for i in range(self.sleep_for_loading):
                sys.stdout.write(f"\rNow loading [{('#' * int(((i+1)/self.sleep_for_loading)/0.05)).ljust(20, '-')}]")
            print()
            html = driver.page_source.encode("utf-8")

        soup = BeautifulSoup(html, "html.parser")
        # This function is not necessary, but you can trim `DecomposeSoupTags` from the soup 
        # and it will help with debugging .
        if len(self.DecomposeSoupTags)>0:
            decoCounts = {tag:0 for tag in self.DecomposeSoupTags+[None]}
            for decoTag in soup.find_all(name=self.DecomposeSoupTags):
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

    def get_contents_from_soup_sections(self, soup_sections):
        """ Get text for each soup section.
        @params soup_sections : (list) Each element is (bs4.element.Tag)
        @return contents      : (list) Each element is dict (key is `en`, `img`, or `headline`).
        """
        contents = []
        print("Contents of the paper")
        print("="*30)
        # for section in soup_sections:
        #     headline = section.find("h2")
        #     contents.extend(self.organize_soup_section(section=section, headline=headline))
        return contents

    def organize_soup_section(self, section, headline="", headline_is_not_added=True):
        """ Organize soup section """
        contents = []
        splitted_soup = split_soup(soup=section, name="img")
        for element in splitted_soup:
            content = {}
            if element.name == "img":
                content["img"] = src2base64(element)
            else:
                content["en"] = element.get_text()
                if headline_is_not_added:
                    content["headline"] = headline
                    headline_is_not_added = False
            contents.append(content)
        return contents 

    # ================== #
    #  crawl_type="tex"  #
    # ================== #

    def get_contents_tex(self, url, driver=None):
        """ Get contents from url by parsing TeX sources.
        @params url      : (str)  page url
        @params driver   : (WebDriver) webdriver
        @return title    : (str)  Title of paper
        @return contents : (list) Each element is dict (key is `en`, `img`, or `headline`).
        """
        tex = self.get_tex_source(url=url, driver=driver)
        title = self.get_title_from_tex(tex)
        tex_sections = self.get_sections_from_tex(tex)
        contents = self.get_contents_from_tex_sections(tex_sections)
        return (title, contents)

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
        for decompose in self.DecomposeTexTags:
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

    def get_contents_from_tex_sections(self, tex_sections):
        """ Get text for each tex section.
        @params soup_sections : (list) Each element is plain text (str)
        @return contents      : (list) Each element is dict (key is `en`, `img`, or `headline`).
        """
        contents = []
        print("Contents of the paper")
        print("="*30)
        return contents

class NatureCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
        )
        self.AvoidAriaLabel = [None,'Ack1','Bib1','additional-information','article-comments','article-info','author-information','ethics','further-reading','rightslink']

    def get_title_from_soup(self, soup):
        title = soup.find(name="h1", attrs={"class" : "c-article-title"}).text
        return title

    def get_sections_from_soup(self, soup):
        sections = [e for e in soup.find_all(name="section") if e.get("aria-labelledby") not in self.AvoidAriaLabel]
        # If the paper is old version, it may not be possible to obtain the content by the above way.
        if len(sections)==0:
            sections = soup.find_all(name="div", class_="c-article-section__content")
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        for section in soup_sections:
            headline = section.get("aria-labelledby")
            h2Tag = section.find("h2")#, class_="c-article-section__title")
            if h2Tag is not None:
                headline = h2Tag.get_text()
                h2Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
        return contents

class arXivCrawler(GummyAbstJournal):
    def __init__(self, sleep_for_loading=3, **kwargs):
        super().__init__(
            crawl_type="tex", 
            gateway="useless",
            sleep_for_loading=sleep_for_loading,
            DecomposeTexTags=["<cit.>", "\xa0", "<ref>"],
        )
        self.AvoidAriaLabel = [None, 'Bib1', 'additional-information', 'article-comments', 'article-info', 'author-information', 'ethics', 'further-reading', 'rightslink']

    def get_contents_tex(self, url, driver=None):
        """ Get contents from url by parsing TeX sources.
        @params url      : (str)  page url
        @params driver   : (WebDriver) webdriver
        @return title    : (str)  Title of paper
        @return contents : (list) Each element is dict (key is `en`, `img`, or `headline`).
        """
        arXiv_no = url.split("/")[-1] # re.findall(pattern=r".*?\/?(\d+\.\d+)", string=url)[0]
        tex = self.get_tex_source(url=f"https://arxiv.org/e-print/{arXiv_no}", driver=None)
        # title = self.get_title_from_tex(tex)
        soup = self.get_soup_source(url=f"https://arxiv.org/abs/{arXiv_no}", driver=None)
        title = self.get_title_from_soup(soup)
        tex_sections = self.get_sections_from_tex(tex)
        contents = self.get_contents_from_tex_sections(tex_sections)
        return (title, contents)
        
    def get_title_from_tex(self, tex):
        raise NotImplementedError("Not Impremented.")

    def get_sections_from_tex(self, tex):
        sections = tex.replace("§.§", "§").split("§")
        return sections   
    
    def get_contents_from_tex_sections(self, tex_sections):
        contents = super().get_contents_from_soup_sections(tex_sections)
        for section in tex_sections:
            content = {}
            first_nl = section.index("\n")
            content["headline"] = section[:first_nl].lstrip(" ").capitalize()
            content["en"] = section[first_nl:].replace("\n", "")
            contents.append(content)
        return contents

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

