# coding: utf-8
import re
import os
import sys
import time
import datetime
import requests
import warnings
from abc import ABCMeta
from bs4 import BeautifulSoup
from pylatexenc.latex2text import LatexNodes2Text

from . import gateways
from .utils._exceptions import JournalTypeIndistinguishableError
from .utils._path import GUMMY_DIR
from .utils.coloring_utils import toGREEN, toBLUE, toRED, toACCENT
from .utils.compress_utils import extract_from_compressed, is_compressed
from .utils.download_utils import download_file, decide_extension, src2base64
from .utils.generic_utils import mk_class_get, handleKeyError
from .utils.journal_utils import canonicalize, whichJournal
from .utils.monitor_utils import ProgressMonitor
from .utils.outfmt_utils import sanitize_filename
from .utils.pdf_utils import getPDFPages
from .utils.soup_utils import split_soup, find_text, split_soup_by_name

SUPPORTED_CRAWL_TYPES = ["soup", "tex", "pdf"]

class GummyAbstJournal(metaclass=ABCMeta):
    """Abstract Jounal Crawlers
    If you want define your own journal crawlers, please inherit this class and define these methods:
    - crawl_type = "tex":
        - get_contents_soup(self, url, driver)
        - get_contents_tex(self, url, driver=None)
        - * get_contents_tex(self, url, driver=None)
        - * get_sections_from_tex(tex)
        - * get_contents_from_tex_sections(tex_sections)
    - crawl_type = "soup":
        - get_soup_source(self, url, driver)
        - get_contents_tex(self, url, driver=None)
        - * get_contents_tex(self, url, driver=None)
        - * get_sections_from_tex(tex)
        - * get_contents_from_tex_sections(tex_sections)
    - crawl_type = "pdf":
        - get_contents_pdf(self, url, driver=None)
        - get_pdf_source(self, url, driver=None)
        - get_title_from_pdf(self, pdf_gen)
        - get_contents_from_pdf_pages(self, pdf_pages)
    NOTE: Be sure to define the marked (*) functions.
    """
    def __init__(self, crawl_type="soup", gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000,
                 DecomposeTexTags=["<cit.>", "\xa0", "<ref>"], 
                 DecomposeSoupTags=['i','link','meta','noscript','script','style','sup'], **kwargs):
        self.name  = self.__class__.__name__
        self.name_ = re.sub(r"([a-z])([A-Z])", r"\1_\2", self.name).lower()
        self.journal_type = re.sub(pattern=r"^(.*)crawler$", repl=r"\1", string=self.name.lower())
        self.crawl_type = crawl_type.lower()
        self.gateway = gateways.get(gateway, verbose=verbose)
        self.sleep_for_loading = sleep_for_loading
        self.verbose = verbose
        self.maxsize = maxsize
        self.DecomposeTexTags = DecomposeTexTags
        self.DecomposeSoupTags = DecomposeSoupTags
        self.crawled_info = {}

    def _set_crawled_info(self, **kwargs):
        self.crawled_info.update(kwargs)

    @property
    def default_title(self):
        return sanitize_filename(self.crawled_info.get("url", datetime.datetime.now().strftime("%Y-%m-%d@%H.%M.%S")))

    def get_contents_crawl_func(self, crawl_type=None):
        crawl_type = crawl_type or self.crawl_type
        handleKeyError(lst=SUPPORTED_CRAWL_TYPES, crawl_type=crawl_type)
        return self.__getattribute__(f"get_contents_{crawl_type}")

    def get_contents(self, url, driver=None, crawl_type=None, **gatewaykwargs):
        self._set_crawled_info(
            url=url, start_time=datetime.datetime.now().strftime("%Y-%m-%d@%H.%M.%S"),
        )
        crawl_type = crawl_type or self.crawl_type
        if self.verbose: print(f"Crawling Type: {toACCENT(crawl_type)}")
        get_contents_func = self.get_contents_crawl_func(crawl_type=crawl_type)
        title, contents = get_contents_func(url=url, driver=driver, **gatewaykwargs)
        return (title, contents)

    # ================== #
    #  crawl_type="soup" #
    # ================== #

    def get_contents_soup(self, url, driver=None, **gatewaykwargs):
        """ Get contents from url using 'BeautifulSoup'.
        @params url      : (str)  page url
        @params driver   : (WebDriver) webdriver
        @return title    : (str)  Title of paper
        @return contents : (list) Each element is dict (key is `en`, `img`, or `headline`).
        """
        soup = self.get_soup_source(url=url, driver=driver, **gatewaykwargs)
        title = self.get_title_from_soup(soup)
        soup_sections = self.get_sections_from_soup(soup)
        contents = self.get_contents_from_soup_sections(soup_sections)
        self._set_crawled_info(soup=soup, title=title, soup_sections=soup_sections, contents=contents)
        return (title, contents)
        
    def get_soup_source(self, url, driver=None, **gatewaykwargs):
        """ Scrape and get page source from url.
        @params url    : (str) tex file url
        @params driver : (WebDriver) webdriver
        @return soup   : (BeautifulSoup)
        """
        # If url is None, we will use crawled information.
        cano_url = canonicalize(url=url, driver=driver)
        self._set_crawled_info(cano_url=cano_url)
        # If driver is None, we could not use gateway service.
        if driver is None:
            html = requests.get(url=cano_url).content
            if self.verbose: print(f"Get {toBLUE(cano_url)}")
        else:
            driver, fmt_url_func = self.gateway.passthrough(driver=driver, url=cano_url, journal_type=self.journal_type, **gatewaykwargs)
            gateway_fmt_url = fmt_url_func(cano_url=cano_url)
            driver.get(gateway_fmt_url)
            time.sleep(self.sleep_for_loading)
            html = driver.page_source.encode("utf-8")

        soup = BeautifulSoup(html, "html.parser")
        # This function is not necessary, but you can trim `DecomposeSoupTags` from the soup 
        # and it will help with debugging .
        if len(self.DecomposeSoupTags)>0:
            if self.verbose: print(f"\nDecompose unnecessary tags to make it easy to parse.\n{'='*30}")
            decoCounts = {tag:0 for tag in self.DecomposeSoupTags+[None]}
            for decoTag in soup.find_all(name=self.DecomposeSoupTags):
                decoCounts[decoTag.name] += 1
                decoTag.decompose()
            for decoTag, count in decoCounts.items():
                if self.verbose: print(f"Decomposed {toGREEN(f'<{decoTag}>')} tag ({count})")
        return soup

    def get_title_from_soup(self, soup):
        """ Get page title from page source.
        @params soup     : (BeautifulSoup)
        @return title    : (str) page title
        """
        title = find_text(soup=soup, name="h1", not_found=self.default_title)
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
        if self.verbose: print(f"\nShow contents of the paper.\n{'='*30}")
        # for section in soup_sections:
        #     headline = section.find("h2")
        #     contents.extend(self.organize_soup_section(section=section, headline=headline))
        return contents

    def organize_soup_section(self, section, headline="", headline_is_not_added=True):
        """ Organize soup section 
        * Extract an image and display it as base64 format in the section.
        * Get Text.
        * Add headline only to the initial content.
        """
        contents = []
        splitted_soup = split_soup(soup=section, name="img")
        for element in splitted_soup:
            content = {}
            if element.name == "img":
                content["img"] = src2base64(
                    base=self.crawled_info.get("cano_url"), src=element
                )
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
        self._set_crawled_info(tex=tex, title=title, tex_sections=tex_sections, contents=contents)
        return (title, contents)

    def get_tex_source(self, url, driver=None):
        """ Download and get tex source from url.
        @params url    : (str) tex file url
        @params driver : (WebDriver) webdriver
        @return tex    : (str) Plain text of tex sources.
        """
        path = download_file(url=url, dirname=GUMMY_DIR)
        ext = "." + path.split(".")[-1]
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
        if self.verbose: print(f"Show contents of the paper\n{'='*30}")
        return contents

    # ================== #
    #  crawl_type="pdf"  #
    # ================== #

    def get_contents_pdf(self, url, driver=None):
        """ Get contents from url by parsing TeX sources.
        @params url      : (str)  page url
        @params driver   : (WebDriver) webdriver
        @return title    : (str)  Title of paper
        @return contents : (list) Each element is dict (key is `en`, `img`, or `headline`).
        """
        pdf_pages = self.get_pdf_source(url=url, driver=driver)
        title = self.get_title_from_pdf(pdf_pages)
        contents = self.get_contents_from_pdf_pages(pdf_pages)
        self._set_crawled_info(title=title, pdf_pages=pdf_pages, contents=contents)
        return (title, contents)

    def get_pdf_source(self, url, driver=None):
        """ Download and get PDF source from url.
        @params url    : (str) PDF file url or path/to/PDF
        @params driver : (WebDriver) webdriver
        @return tex    : (str) Plain text of tex sources.
        """
        path = url if os.path.exists(url) else download_file(url=url, dirname=GUMMY_DIR)
        pdf_pages = getPDFPages(path=path)
        return pdf_pages

    def get_title_from_pdf(self, pdf_gen):
        title = "title"
        return title

    def get_contents_from_pdf_pages(self, pdf_pages):
        contents = []
        len_pdf_pages = len(pdf_pages)
        for i,page_texts in enumerate(pdf_pages):
            page_no = f"Page.{i+1:>0{len(str(len_pdf_pages))}}/{len_pdf_pages}"
            content = {"headline" : page_no, "en" : ""}
            for text in page_texts:
                if text.startswith('<img src="data:image/jpeg;base64'):
                    contents.append(content)
                    contents.append({"img": text})
                    content = {"en" : ""}
                else:
                    content["en"] += text.replace("-\n", "").replace("\n", " ")
            if len(content)>0:
                contents.append(content)
            if self.verbose: print(page_no)
        return contents

class LocalPDFCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="pdf", 
            gateway="useless",
            sleep_for_loading=3,
            maxsize=maxsize,
        )

    def get_contents_pdf(self, url, driver=None):
        _, contents = super().get_contents_pdf(url=url, driver=driver)
        title = url.split("/")[-1].rstrip(".pdf")
        return title, contents

class NatureCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )
        self.AvoidAriaLabel = [None,'Ack1','Bib1','additional-information','article-comments','article-info','author-information','ethics','further-reading','rightslink']

    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", attrs={"class" : "c-article-title"}, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = [e for e in soup.find_all(name="section") if e.get("aria-labelledby") not in self.AvoidAriaLabel]
        # If the paper is old version, it may not be possible to obtain the content by the above way.
        if len(sections)==0:
            sections = soup.find_all(name="div", class_="c-article-section__content")
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = section.get("aria-labelledby")
            h2Tag = section.find("h2")#, class_="c-article-section__title")
            if h2Tag is not None:
                headline = h2Tag.get_text()
                h2Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class arXivCrawler(GummyAbstJournal):
    def __init__(self, sleep_for_loading=3, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="pdf", 
            gateway="useless",
            sleep_for_loading=sleep_for_loading,
            maxsize=maxsize,
            DecomposeTexTags=["<cit.>", "\xa0", "<ref>"],
        )
        self.AvoidAriaLabel = [None, 'Bib1', 'additional-information', 'article-comments', 'article-info', 'author-information', 'ethics', 'further-reading', 'rightslink']

    @staticmethod
    def get_pdf_url(arXivNo):
        return f"https://arxiv.org/pdf/{arXivNo}.pdf"

    @staticmethod
    def get_abs_url(arXivNo):
        return f"https://arxiv.org/abs/{arXivNo}"

    @staticmethod
    def get_eprint_url(arXivNo):
        return f"https://arxiv.org/e-print/{arXivNo}"

    @staticmethod
    def get_arXivNo(url):
        return re.sub(pattern=r"^.+\/((?:\d|\.)+)(?:\.pdf)?$", repl=r"\1", string=url)

    def get_contents_pdf(self, url, driver=None):
        arXivNo = url.split("/")[-1]
        _, contents = super().get_contents_pdf(url=self.get_pdf_url(arXivNo), driver=None)
        # title = self.get_title_from_tex(tex)
        soup = self.get_soup_source(url=self.get_abs_url(arXivNo), driver=None)
        title = self.get_title_from_soup(soup)
        return (title, contents)

    def get_contents_tex(self, url, driver=None):
        """ Get contents from url by parsing TeX sources.
        @params url      : (str)  page url
        @params driver   : (WebDriver) webdriver
        @return title    : (str)  Title of paper
        @return contents : (list) Each element is dict (key is `en`, `img`, or `headline`).
        """
        arXivNo = self.get_arXivNo(url)
        tex = self.get_tex_source(url=self.get_eprint_url(arXivNo), driver=None)
        # title = self.get_title_from_tex(tex)
        soup = self.get_soup_source(url=self.get_abs_url(arXivNo), driver=None)
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
        len_tex_sections = len(tex_sections)
        for i,section in enumerate(tex_sections):
            content = {}
            first_nl = section.index("\n")
            headline = section[:first_nl].lstrip(" ").capitalize()
            content["headline"] = headline
            content["en"] = section[first_nl:].replace("\n", "")
            contents.append(content)
            if self.verbose: print(f"[{i+1:>0{len(str(len_tex_sections))}}/{len_tex_sections}] {headline}")
        return contents

    def get_title_from_soup(self, soup):
        """ Get page title from page source.
        @params soup     : (BeautifulSoup)
        @return title    : (str) page title
        """
        title = find_text(soup=soup, name="h1", attrs={"class" : "title mathjax"}, not_found=self.default_title).lstrip("Title:")
        return title

class NCBICrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )
        self.AvoidIdsPatterns = [r"^idm[0-9]+", r"^S49$", r"^ass-data$"]

    @property
    def AvoidIdsPattern(self):
        return f"(?:{'|'.join([f'(?:{pat})' for pat in self.AvoidIdsPatterns])})"

    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", class_="content-title", not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = [e for e in soup.find_all(name="div", class_="tsec") if re.match(pattern=self.AvoidIdsPattern, string=e.get("id")) is None]
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = "headline"
            h2Tag = section.find("h2")#, class_="c-article-section__title")
            if h2Tag is not None:
                headline = h2Tag.get_text().strip()
                h2Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class PubMedCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )
        self.AvoidIdsPatterns = [r"^idm[0-9]+", r"^S49$", r"^ass-data$"]

    def get_contents_soup(self, url, driver=None, **gatewaykwargs):
        soup = self.get_soup_source(url=url, driver=driver, **gatewaykwargs)
        a_doi = soup.find(name="a", class_="id-link")
        if a_doi is not None:
            cano_url = canonicalize(url=a_doi.get("href"), driver=driver, sleep_for_loading=5)
            if cano_url!=url:
                try:
                    journal_type = whichJournal(url=cano_url, driver=None, verbose=self.verbose)
                    if journal_type!="pubmed": # Prevent infinite loop
                        crawler = get(journal_type, gateway=self.gateway, sleep_for_loading=3, verbose=self.verbose)
                        return crawler.get_contents(url=cano_url, driver=driver)
                except JournalTypeIndistinguishableError:
                    if self.verbose: print(f"{toGREEN('gummy.utils.journal_utils.whichJournal')} could not distinguish the journal type, so Scraping from PubMed")
        title = self.get_title_from_soup(soup)
        soup_sections = self.get_sections_from_soup(soup)
        contents = self.get_contents_from_soup_sections(soup_sections)
        self._set_crawled_info(soup=soup, title=title, soup_sections=soup_sections, contents=contents)
        return (title, contents)

    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", class_="heading-title", strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = soup.find_all(name="div", class_="abstract")
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = section.get("aria-labelledby")
            h2Tag = section.find("h2", class_="title")
            if h2Tag is not None:
                headline = h2Tag.get_text()
                h2Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class OxfordAcademicCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )
    
    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", class_="article-title-main", strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = soup.find_all(name=(("h2","h3","h4"), "p", "div"), class_=(("abstract-title", "section-title"), "chapter-para", "fig-section"))
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            tag = section.name
            if tag in ["h2", "h3", "h4"]:
                headline = section.text
                contents.append({"headline" : headline})
            elif tag =="p":
                headline = "\t" + " ".join(section.get_text().split(" ")[:3]) + "..."
                contents.extend(self.organize_soup_section(section=section, headline_is_not_added=False))
            elif tag=="div":
                divTag = section.find(name="div", class_="fig-label")
                if divTag is not None:
                    headline = divTag.get_text()
                    divTag.decompose()
                else:
                    headline = "<figure>"
                headline = "\t" + headline
                contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class ScienceDirect(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )

    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="span", class_="title-text", strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = soup.find_all(name="div", class_="Abstracts")
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        headline = ""
        for i,section in enumerate(soup_sections):
            h2Tag = section.find("h2", class_="section-title")
            if h2Tag is not None:
                headline = h2Tag.get_text()
                h2Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class SpringerCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )
        self.AvoidAriaLabel = [None,'Ack1','Bib1','additional-information','article-comments','article-info','author-information','ethics','further-reading','rightslink']

    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", class_="c-article-title", strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = [e for e in soup.find_all(name="section") if e.get("aria-labelledby") not in self.AvoidAriaLabel]
        if len(sections)==0:
            sections = [e for e in soup.find_all(name="section") if e.get("Abs1") not in self.AvoidAriaLabel]
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = section.get("aria-labelledby")
            h2Tag = section.find("h2")#, class_="c-article-section__title")
            if h2Tag is not None:
                headline = h2Tag.get_text()
                h2Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class MDPICrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )
        self.AvoidAriaLabel = [None,'Ack1','Bib1','additional-information','article-comments','article-info','author-information','ethics','further-reading','rightslink']

    def get_soup_source(self, url, driver=None, **gatewaykwargs):
        # If url is None, we will use crawled information.
        cano_url = canonicalize(url=url, driver=driver)
        cano_url = cano_url.rstrip("/htm")+"/htm"
        soup = super().get_soup_source(url=cano_url, driver=driver, **gatewaykwargs)
        return soup

    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", class_="title", strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = soup.find_all(name="section", attrs={"type" : "other"})
        sections = [e for e in soup.find_all(name="section") if e.get("aria-labelledby") not in self.AvoidAriaLabel]
        abst = soup.find(name="div", class_="art-abstract")
        if abst is not None:
            abst_section = soup.new_tag(name="section", attrs={"type" : "other"})
            abst_h2Tag = soup.new_tag(name="h2")
            abst_h2Tag.string = "0. Abstract"
            abst_section.append(abst_h2Tag)
            abst_section.append(abst)
            sections.insert(0, abst_section)
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = section.get("id")
            h2Tag = section.find("h2")
            if h2Tag is not None:
                headline = h2Tag.get_text()
                h2Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class FEBSPRESSCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )

    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", class_="citation__title", strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = soup.find_all(name="section", class_=("article-section__abstract", "article-section__content"))
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = section.get("id")
            h2Tag = section.find("h2")#
            if h2Tag is not None:
                headline = h2Tag.get_text()
                h2Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class UniOKLAHOMACrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )

    def get_title_from_soup(self, soup):
        sections = soup.find_all(name="p", class_="a")
        if len(sections)>2:
            title = sections[1].get_text()
        else:
            title = self.default_title
        return title

    def get_sections_from_soup(self, soup):
        sections = soup.find_all(name="p", class_=("a", "a0", "MsoNormal"))[2:]
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            contents.extend(self.organize_soup_section(section=section, headline="", headline_is_not_added=False))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}]")
        return contents

class LungCancerCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )
        self.AvoidHeadlines = ['', 'Keywords', 'References', 'Article Info', 'Publication History', 'Identification', 'Copyright', 'ScienceDirect']

    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", class_="article-header__title", strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = [e for e in soup.find_all(name="section") if find_text(soup=e, name=("h2", "h3"), not_found="") not in self.AvoidHeadlines]
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = "headline"
            h2h3Tag = section.find(name=("h2", "h3"))
            if h2h3Tag is not None:
                headline = h2h3Tag.get_text()
                h2h3Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class CellPressCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )
        self.AvoidDataLeftHandNavs = [None, "Acknowledgements", "References"]
    
    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", class_="article-header__title", strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = [e for e in soup.find_all(name="section") if e.find(name="h2") is not None and e.find(name="h2").get("data-left-hand-nav") not in self.AvoidDataLeftHandNavs]
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = "headline"
            h2Tag = section.find(name="h2")
            if h2Tag is not None:
                headline = h2Tag.get_text()
                h2Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class WileyOnlineLibraryCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )
    
    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", class_="citation__title", strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = soup.find_all(name="section", class_=("article-section article-section__abstract"))
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = "headline"
            h3Tag = section.find(name="h3")
            if h3Tag is not None:
                headline = h3Tag.get_text()
                h3Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class JBCCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )
    
    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", attrs={"id": "article-title-1"}, strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = soup.find_all(name="div", class_=("section abstract"))
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = "headline"
            h2Tag = section.find(name="h2")
            if h2Tag is not None:
                headline = h2Tag.get_text()
                h2Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class BiologistsCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )
        self.AvoidIDs = ["ack", "fn-group", "ref-list"]
    
    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="div", class_="highwire-cite-title", strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = [e for e in soup.find_all(name="div", class_="section") if not any([e.get("id", self.AvoidIDs[0]).startswith(id) for id in self.AvoidIDs])]
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = section.get("id")
            h2Tag = section.find(name="h2")
            if h2Tag is not None:
                headline = h2Tag.get_text()
                h2Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class BioMedCentralCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )
        self.AvoidAriaLabel = [None,'Ack1','Bib1','additional-information','article-comments','article-info','author-information','ethics','further-reading','rightslink','Sec2','Sec3']
    
    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", class_="c-article-title", strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = [e for e in soup.find_all(name="section") if e.get("aria-labelledby") not in self.AvoidAriaLabel]
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = section.get("aria-labelledby")
            h2Tag = section.find("h2")
            if h2Tag is not None:
                headline = h2Tag.get_text()
                h2Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class IEEEXploreCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=10, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )
    
    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", class_="document-title", strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = []
        # Abstract
        abst = soup.find(name="div", class_="abstract-text")
        if abst is not None:
            abst_div_section = soup.new_tag(name="div", class_="section")
            abst_strong = abst.find(name="strong")
            if abst_strong is not None:
                abst_strong.decompose()
            abst_divTag = soup.new_tag(name="div", class_="header")
            abst_divTag.string = "Abstract"
            abst_div_section.append(abst_divTag)
            abst_div_section.append(abst)
            sections.append(abst_div_section)
        # Other article
        article = soup.find(name="div", id="article")
        if article is not None:
            sections.extend(article.find_all(name="div", class_="section"))
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = "headline"
            divTag = section.find(name="div", class_="header")
            if divTag is not None:
                headline = divTag.get_text().strip()
                divTag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class JSTAGECrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )
    
    def get_soup_source(self, url, driver=None, **gatewaykwargs):
        cano_url = canonicalize(url=url, driver=driver)
        if self.verbose: print(f"You can download PDF from {toBLUE(cano_url.replace('_article', '_pdf/-char/en'))}")
        soup = super().get_soup_source(url=cano_url, driver=driver, **gatewaykwargs)
        return soup

    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="div", class_="global-article-title", strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = soup.find_all(name="div", attrs={"id": "article-overiew-abstract-wrap"})
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = "headline"
            divTag = section.find(name="div")
            if divTag is not None:
                headline = divTag.get_text().strip()
                divTag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class ACSPublicationsCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )
    
    def get_soup_source(self, url, driver=None, **gatewaykwargs):
        cano_url = canonicalize(url=url, driver=driver)
        if self.verbose: print(f"You can download PDF from {toBLUE(cano_url.replace('/doi/', '/doi/pdf/'))}")
        soup = super().get_soup_source(url=cano_url, driver=driver, **gatewaykwargs)
        return soup

    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", class_="article_header-title", strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = soup.find_all(name="div", class_="article_abstract")
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = "headline"
            h2Tag = section.find(name="h2")
            if h2Tag is not None:
                headline = h2Tag.get_text().strip()
                h2Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class StemCellsCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )
    
    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", class_="citation__title", strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = soup.find_all(name="section", class_=("article-section__abstract", "article-section__content"))
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = "headline"
            h2Tag = section.find(name="h2")
            if h2Tag is not None:
                headline = h2Tag.get_text()
                h2Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class KeioUniCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )

    def get_contents_soup(self, url, driver=None, **gatewaykwargs):
        soup = self.get_soup_source(url=url, driver=driver, **gatewaykwargs)
        div_doi = soup.find(name="div", class_="doi")
        if div_doi is not None:
            a_doi = div_doi.find(name="a")
            if a_doi is not None:
                cano_url = canonicalize(url=a_doi.get("href"), driver=driver, sleep_for_loading=5)
                if cano_url!=url:
                    try:
                        journal_type = whichJournal(url=cano_url, driver=None, verbose=self.verbose)
                        if journal_type!="unikeio": # Prevent infinite loop
                            crawler = get(journal_type, gateway=self.gateway, sleep_for_loading=3, verbose=self.verbose)
                            return crawler.get_contents(url=cano_url, driver=driver)
                    except JournalTypeIndistinguishableError:
                        if self.verbose: print(f"{toGREEN('gummy.utils.journal_utils.whichJournal')} could not distinguish the journal type, so Scraping from PubMed")
        title = self.get_title_from_soup(soup)
        soup_sections = self.get_sections_from_soup(soup)
        contents = self.get_contents_from_soup_sections(soup_sections)
        self._set_crawled_info(soup=soup, title=title, soup_sections=soup_sections, contents=contents)
        return (title, contents)
    
    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = soup.find_all(name="div", class_="rendering_contributiontojournal_abstractportal")
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = section.get("class", ["Abstract"])[-1]
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class PLOSONECrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )
    
    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", attrs={"id": "artTitle"}, strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = soup.find_all(name="div", class_="toc-section")
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = "headline"
            h2Tag = section.find(name="h2")
            if h2Tag is not None:
                headline = h2Tag.get_text().strip()
                h2Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class frontiersCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )
    
    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = soup.find_all(name="div", class_="JournalAbstract")
        text_section = soup.find(name="div", class_="JournalFullText")
        if text_section is not None:
            sections.extend(split_soup_by_name(soup=text_section, name="h2"))
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = "headline"
            h1h2Tag = section.find(name=("h1", "h2"))
            if h1h2Tag is not None:
                headline = h1h2Tag.get_text().strip()
                h1h2Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class RNAjournalCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )
    
    def get_soup_source(self, url, driver=None, **gatewaykwargs):
        cano_url = canonicalize(url=url, driver=driver)
        if self.verbose: print(f"You can download PDF from {toBLUE(cano_url + '.full.pdf')}")
        soup = super().get_soup_source(url=cano_url, driver=driver, **gatewaykwargs)
        return soup

    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", attrs={"id": "article-title-1", "itemprop": "headline"}, strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = soup.find_all(name="div", class_="section")
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = "headline"
            h2Tag = section.find(name="h2")
            if h2Tag is not None:
                headline = h2Tag.get_text().strip()
                h2Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class IntechOpenCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )
    
    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", class_="title", strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = soup.find_all(name="div", class_="intro")
        body = soup.find(name="div", class_="reader-body")
        if body is not None:
            sections.extend(body.find_all(name="div", class_="section"))
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = "headline"
            h2Tag = section.find(name="h2")
            if h2Tag is not None:
                headline = h2Tag.get_text().strip()
                h2Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class NRCResearchPressCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )
    
    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", class_="article-title", strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = soup.find_all(name="div", class_="box-pad border-lightgray margin-bottom")
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = "headline"
            h2Tag = section.find(name="h2")
            if h2Tag is not None:
                headline = h2Tag.get_text().strip()
                h2Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class SpandidosCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )
    
    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", attrs={"id": "titleId"}, strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = soup.find_all(name="div", attrs={"id": "articleAbstract"})
        try:
            sections.extend(split_soup_by_name(sections[0].next.next.next, name=("h4", "h5")))
        except AttributeError:
            if self.verbose: print("Use only Abstract.")
        except IndexError:
            if self.verbose: print(toRED("Couldn't scrape well."))
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = "headline"
            h4h5Tag = section.find(name=("h4", "h5"))
            if h4h5Tag is not None:
                headline = h4h5Tag.get_text().strip()
                h4h5Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents
    
class TaylorandFrancisOnlineCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )
    
    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", attrs={"id": "titleId"}, strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = soup.find_all(name="div", class_=("hlFld-Abstract","NLM_sec NLM_sec-type_intro NLM_sec_level_1"))
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = "headline"
            h2Tag = section.find(name="h2")
            if h2Tag is not None:
                headline = h2Tag.get_text().strip()
                h2Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class bioRxivCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )
        self.AvoidIDs = ["ref-list-1"]

    def get_soup_source(self, url, driver=None, **gatewaykwargs):
        # If url is None, we will use crawled information.
        # https://www.biorxiv.org/content/10.1101/2020.05.14.095356v1
        cano_url = canonicalize(url=url, driver=driver)
        cano_url = cano_url + ".full"
        soup = super().get_soup_source(url=cano_url, driver=driver, **gatewaykwargs)
        return soup

    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", attrs={"id":"page-title", "class": "highwire-cite-title"}, strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = soup.find_all(name="div", class_="article fulltext-view")
        if len(sections)>0:
            sections = [e for e in sections[0].find_all(name="div", class_="section") if e.get("id") not in self.AvoidIDs]
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = "headline"
            h2h3Tag = section.find(name=("h2","h3"))
            if h2h3Tag is not None:
                headline = h2h3Tag.get_text().strip()
                h2h3Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class RSCCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )

    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h2", class_="capsule__title", strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = soup.find_all(name="div", class_="capsule__column-wrapper")
        text_section = soup.find(name="div", attrs={"id": "pnlArticleContent"})
        if text_section is not None:
            sections.extend(split_soup_by_name(soup=text_section, name="h2"))
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = "headline"
            h2Tag = section.find(name=("h2"))
            if h2Tag is not None:
                headline = h2Tag.get_text().strip()
                h2Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class JSSECrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="pdf", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )

    @staticmethod
    def get_jsseNo(url):
        return re.sub(pattern=r"^.*\/index.php\/jsse\/article\/(?:view|download)\/([0-9]+)(?:\/[0-9]+)?$", repl=r"\1", string=url)
    
    @staticmethod
    def get_abs_url(jsseNo):
        return f"https://www.jsse.org/index.php/jsse/article/view/{jsseNo}"
    
    @staticmethod
    def get_html_url(jsseNo):
        soup = BeautifulSoup(markup=requests.get(JSSECrawler.get_abs_url(jsseNo)).content, features="html.parser")
        return soup.find(name="a", class_="obj_galley_link pdf").get("href")
        
    @staticmethod
    def get_pdf_url(jsseNo):
        return JSSECrawler.get_html_url(jsseNo).replace("/view/", "/download/")

    def get_contents_pdf(self, url, driver=None):
        jsseNo = self.get_jsseNo(url)
        _, contents = super().get_contents_pdf(url=self.get_pdf_url(jsseNo), driver=None)
        soup = self.get_soup_source(url=self.get_abs_url(jsseNo), driver=None)
        title = self.get_title_from_soup(soup)
        return (title, contents)

    def get_soup_source(self, url, driver=None, **gatewaykwargs):
        jsseNo = self.get_jsseNo(url)
        soup = super().get_soup_source(url=self.get_abs_url(jsseNo), driver=driver, **gatewaykwargs)
        return soup

    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", class_="page_title", strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = soup.find_all(name="div", class_="item abstract")
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = "headline"
            h3Tag = section.find("h3")
            if h3Tag is not None:
                headline = h3Tag.get_text()
                h3Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class ScienceAdvancesCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="soup", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )
        self.AvoidIDs = ["ref-list-1"]

    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", class_="article__headline", strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        article = soup.find(name="article", class_="primary primary--content")
        if article is not None:
            soup = article
        sections = [e for e in soup.find_all(name="div", class_="section") if e.get("id") not in self.AvoidIDs]
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = section.get("id", "headline")
            h2Tag = section.find(name=("h2"))
            if h2Tag is not None:
                headline = h2Tag.get_text().strip()
                h2Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class medRxivCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="pdf", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )

    @staticmethod
    def get_abs_url(url):
        return re.sub(pattern=r"(^.*\/.*?v[0-9]+)(\..+)?", repl=r"\1", string=url)
            
    @staticmethod
    def get_pdf_url(url):
        return medRxivCrawler.get_abs_url(url) + ".full.pdf"

    def get_contents_pdf(self, url, driver=None):
        _, contents = super().get_contents_pdf(url=self.get_pdf_url(url), driver=None)
        soup = self.get_soup_source(url=self.get_abs_url(url), driver=None)
        title = self.get_title_from_soup(soup)
        return (title, contents)

    def get_soup_source(self, url, driver=None, **gatewaykwargs):
        soup = super().get_soup_source(url=self.get_abs_url(url), driver=driver, **gatewaykwargs)
        return soup

    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h1", attrs={"class": "highwire-cite-title", "id": "page-title"}, strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = soup.find_all(name="div", class_="section")
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = section.get("id", "headline")
            h2Tag = section.find("h2")
            if h2Tag is not None:
                headline = h2Tag.get_text()
                h2Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

class ACLAnthologyCrawler(GummyAbstJournal):
    def __init__(self, gateway="useless", sleep_for_loading=3, verbose=True, maxsize=5000, **kwargs):
        super().__init__(
            crawl_type="pdf", 
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            maxsize=maxsize,
        )

    @staticmethod
    def get_abs_url(url):
        return url.rstrip("/").rstrip(".pdf")
            
    @staticmethod
    def get_pdf_url(url):
        return ACLAnthologyCrawler.get_abs_url(url) + ".pdf"

    def get_contents_pdf(self, url, driver=None):
        _, contents = super().get_contents_pdf(url=self.get_pdf_url(url), driver=None)
        soup = self.get_soup_source(url=self.get_abs_url(url), driver=None)
        title = self.get_title_from_soup(soup)
        return (title, contents)

    def get_soup_source(self, url, driver=None, **gatewaykwargs):
        soup = super().get_soup_source(url=self.get_abs_url(url), driver=driver, **gatewaykwargs)
        return soup

    def get_title_from_soup(self, soup):
        title = find_text(soup=soup, name="h2", attrs={"id": "title"}, strip=True, not_found=self.default_title)
        return title

    def get_sections_from_soup(self, soup):
        sections = soup.find_all(name="div", class_="card-body acl-abstract")
        return sections

    def get_contents_from_soup_sections(self, soup_sections):
        contents = super().get_contents_from_soup_sections(soup_sections)
        len_soup_sections = len(soup_sections)
        for i,section in enumerate(soup_sections):
            headline = "headline"
            h5Tag = section.find("h5")
            if h5Tag is not None:
                headline = h5Tag.get_text()
                h5Tag.decompose()
            contents.extend(self.organize_soup_section(section=section, headline=headline))
            if self.verbose: print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {headline}")
        return contents

all = TranslationGummyJournalCrawlers = {
    "pdf"              : LocalPDFCrawler,
    "arxiv"            : arXivCrawler, 
    "nature"           : NatureCrawler,
    "ncbi"             : NCBICrawler,
    "pubmed"           : PubMedCrawler,
    "oxfordacademic"   : OxfordAcademicCrawler,
    "sciencedirect"    : ScienceDirect,
    "springer"         : SpringerCrawler,
    "mdpi"             : MDPICrawler,
    "febs"             : FEBSPRESSCrawler,
    "unioklahoma"      : UniOKLAHOMACrawler,
    "lungcancer"       : LungCancerCrawler,
    "cellpress"        : CellPressCrawler,
    "wiley"            : WileyOnlineLibraryCrawler,
    "jbc"              : JBCCrawler,
    "biologists"       : BiologistsCrawler,
    "bmc"              : BioMedCentralCrawler,
    "ieee"             : IEEEXploreCrawler,
    "jstage"           : JSTAGECrawler,
    "acs"              : ACSPublicationsCrawler,
    "stemcells"        : StemCellsCrawler,
    "unikeio"          : KeioUniCrawler,
    "plosone"          : PLOSONECrawler,
    "frontiers"        : frontiersCrawler,
    "rnajournal"       : RNAjournalCrawler,
    "intechopen"       : IntechOpenCrawler,
    "nrcresearchpress" : NRCResearchPressCrawler,
    "spandidos"        : SpandidosCrawler,
    "tandfonline"      : TaylorandFrancisOnlineCrawler,
    "biorxiv"          : bioRxivCrawler,
    "rsc"              : RSCCrawler,
    "jsse"             : JSSECrawler,
    "scienceadvances"  : ScienceAdvancesCrawler,
    "medrxiv"          : medRxivCrawler,
    "aclanthology"     : ACLAnthologyCrawler,
}

get = mk_class_get(
    all_classes=TranslationGummyJournalCrawlers,
    gummy_abst_class=[GummyAbstJournal],
    genre="journals"
)

