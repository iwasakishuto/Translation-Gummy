# coding: utf-8
"""These classes get contents from paper pages ( ``html`` ) or files ( ``PDF``, ``TeX``)

Supported journals are listed `here (Supported journals · iwasakishuto/Translation-Gummy Wiki) <https://github.com/iwasakishuto/Translation-Gummy/wiki/Supported-journals>`_,
and if you want to support for new journals, please request on twitter DM |twitter badge| or `Github issues <https://github.com/iwasakishuto/Translation-Gummy/issues>`_.

You can easily get (import) ``Journal Crawler Class`` by the following ways.

.. code-block:: python

    >>> from gummy import journals
    >>> crawler = journals.get("nature")
    >>> crawler
    <gummy.journals.NatureCrawler at 0x1256777c0>
    >>> from gummy.journals import NatureCrawler
    >>> nature = NatureCrawler()
    >>> nature
    <gummy.journals.NatureCrawler at 0x1253da9a0>
    >>> crawler = journals.get(nature)
    >>> id(crawler) == id(nature)
    True

.. |twitter badge| image:: https://img.shields.io/badge/twitter-Requests-1da1f2?style=flat-square&logo=twitter
   :target: https://www.twitter.com/messages/compose?recipient_id=1042783905697288193&text=Please%20support%20this%20journal%3A%20
"""
import os
import re
import urllib
from abc import ABCMeta
from dataclasses import dataclass
from posixpath import split
from typing import Any, Callable, Dict, List, Optional, Tuple, TypedDict, Union

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from pdfminer.layout import LTItem
from pylatexenc.latex2text import LatexNodes2Text
from requests.exceptions import RequestException
from selenium.webdriver.remote.webdriver import WebDriver

from . import gateways
from .utils._exceptions import JournalTypeIndistinguishableError
from .utils._path import GUMMY_DIR
from .utils._type import T_PAPER_CONTENT, T_PAPER_TITLE_CONTENTS
from .utils.coloring_utils import toACCENT, toBLUE, toGREEN, toRED
from .utils.compress_utils import extract_from_compressed, is_compressed
from .utils.download_utils import download_file, src2base64
from .utils.driver_utils import scrollDown, try_find_element_click, wait_until_all_elements
from .utils.generic_utils import flatten_dual, handleKeyError, mk_class_get, now_str, str_strip, verbose2print
from .utils.journal_utils import canonicalize, whichJournal
from .utils.outfmt_utils import sanitize_filename
from .utils.pdf_utils import get_pdf_contents
from .utils.soup_utils import (
    find_target_id,
    find_target_text,
    group_soup_with_head,
    kwargs2tag,
    replace_soup_tag,
    split_section,
    str2soup,
)

SUPPORTED_CRAWL_TYPES: List[str] = ["soup", "tex", "pdf"]


class GummyAbstJournal(metaclass=ABCMeta):
    """If you want define your own journal crawlers, please inherit this class and define these methods:

    - if ``crawl_type`` == ``"tex"``:
        - :meth:`get_contents_tex(self, url, driver=None) <gummy.journals.GummyAbstJournal.get_contents_tex>`
        - (required) get_contents_tex(self, url, driver=None)
        - (required) get_sections_from_tex(tex)
        - (required) get_contents_from_tex_sections(tex_sections)
    - if ``crawl_type`` == ``"soup"``:
        - :meth:`get_soup_source(self, url, driver=None, **gatewaykwargs) <gummy.journals.GummyAbstJournal.get_soup_source>`
        - :meth:`get_contents_soup(self, url, driver=None, **gatewaykwargs) <gummy.journals.GummyAbstJournal.get_contents_soup>`
        - (if necessary) :meth:`get_contents_from_soup_sections(self, soup_sections) <gummy.journals.GummyAbstJournal.get_contents_from_soup_sections>`
        - (required) :meth:`get_title_from_soup(self, soup) <gummy.journals.GummyAbstJournal.get_title_from_soup>`
        - (required) :meth:`get_sections_from_soup(self, soup) <gummy.journals.GummyAbstJournal.get_sections_from_soup>`
        - (required) :meth:`get_head_from_section(self, section) <gummy.journals.GummyAbstJournal.get_head_from_section>`
        - (if necessary) :meth:`make_elements_visible(self, driver) <gummy.journals.GummyAbstJournal.make_elements_visible>`
        - :meth:`decompose_soup_tags(self, soup) <gummy.journals.GummyAbstJournal.decompose_soup_tags>`
        - :meth:`organize_soup_section(self, section, head="", head_is_not_added=True) <gummy.journals.GummyAbstJournal.organize_soup_section>`
    - if ``crawl_type`` == ``"pdf"``:
        - :meth:`get_contents_pdf(self, url, driver=None) <gummy.journals.GummyAbstJournal.get_contents_pdf>`
        - :meth:`get_pdf_source(self, url, driver=None) <gummy.journals.GummyAbstJournal.get_pdf_source>`
        - :meth:`get_title_from_pdf(self, pdf_gen) <gummy.journals.GummyAbstJournal.get_title_from_pdf>`
        - :meth:`get_contents_from_pdf_pages(self, pdf_pages) <gummy.journals.GummyAbstJournal.get_contents_from_pdf_pages>`

    Args:
        crawl_type (str)            : Crawling type, if you not specify, use recommended crawling type.
        gateway (str, GummyGateWay) : identifier of the Gummy Gateway Class. See :mod:`gateways <gummy.gateways>`. (default= ``None`` )
        sleep_for_loading (int)     : Number of seconds to wait for a web page to load (default= ``3`` )
        verbose (bool)              : Whether you want to print output or not. (default= ``True`` )
        DecomposeTexTags (list)     : Tex tags to be removed in advance for easier analysis. (default= ``["<cit.>","\xa0","<ref>"]`` )
        DecomposeSoupTags (list)    : HTML tags to be removed in advance for easier analysis. (default= ``["i","link","meta","noscript","script","style","sup"]`` )
        isSubheadTags (Callable)    : HTML tag names to identify the subheadings.
        kwargs (dict)               : There is no use for it so far.

    Attributes:
        crawling_logs (dict)        : Crawling logs.
    """

    def __init__(
        self,
        crawl_type: str = "soup",
        gateway: str = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        DecomposeTexTags: List[str] = ["<cit.>", "\xa0", "<ref>"],
        DecomposeSoupTags: List[Dict[str, Any]] = [
            {"name": "link"},
            {"name": "meta"},
            {"name": "noscript"},
            {"name": "script"},
            {"name": "style"},
            # {"name": "sup"},
        ],
        isSubheadTags: Callable[[Tag], bool] = lambda tag: False,
        isSubSection: Callable[[Tag], bool] = lambda tag: False,
        isFigCaption: Callable[[Tag], bool] = lambda tag: tag.name == "figcaption",
        **kwargs,
    ):
        handleKeyError(lst=SUPPORTED_CRAWL_TYPES, crawl_type=crawl_type)
        self.crawl_type: str = crawl_type
        self.gateway: gateways.GummyAbstGateWay = gateways.get(gateway, verbose=verbose)
        self.sleep_for_loading: int = sleep_for_loading
        self.verbose: bool = verbose
        self.DecomposeTexTags: List[str] = DecomposeTexTags
        self.DecomposeSoupTags: List[Dict[str, Any]] = DecomposeSoupTags
        self.isSubheadTags: Callable[[Tag], bool] = isSubheadTags
        self.isSubSection: Callable[[Tag], bool] = isSubSection
        self.isFigCaption: Callable[[Tag], bool] = isFigCaption
        self.crawling_logs: Dict[str, Any] = {}
        self.__dict__.update(kwargs)
        self.print = verbose2print(verbose=verbose)

    @property
    def class_name(self) -> str:
        """Same as ``self.__class__.__name__``."""
        return self.__class__.__name__

    @property
    def name(self) -> str:
        """Translator service name."""
        return self.class_name.replace("Crawler", "")

    @property
    def journal_type(self) -> str:
        """Journal Type."""
        return self.name.lower()

    def _store_crawling_logs(self, **kwargs) -> None:
        """Store ``kwargs`` in ``self.crawling_logs``"""
        self.crawling_logs.update(kwargs)

    @property
    def default_title(self) -> str:
        """Default title."""
        return sanitize_filename(fp=self.crawling_logs.get("url", now_str()))

    def get_contents(
        self, url: str, driver: Optional[WebDriver] = None, crawl_type: Optional[str] = None, **gatewaykwargs
    ) -> Tuple[str, T_PAPER_CONTENT]:
        """Get contents using the method which is determined based on ``crawl_type``

        Args:
            url (str)            : URL of a paper or ``path/to/local.file``.
            driver (WebDriver)   : Selenium WebDriver.
            crawl_type (str)     : Crawling type, if you not specify, use recommended crawling type.
            gatewaykwargs (dict) : Gateway keywargs. See :meth:`passthrough <gummy.gateways.GummyAbstGateWay.passthrough>`.

        Returns:
            tuple (str, dict) : (title, content)

        Examples:
            >>> from gummy import journals
            >>> crawler = journals.get("nature")
            >>> title, texts = crawler.get_contents(url="https://www.nature.com/articles/ncb0800_500")
            Crawling Type: soup
                :
            >>> print(title)
            Formation of the male-specific muscle in female by ectopic expression
            >>> print(texts[:1])
            [{'head': 'Abstract', 'raw': 'The  () gene product Fru has been ... for the sexually dimorphic actions of the gene.'}]
        """
        self._store_crawling_logs(url=url, start_time=now_str())
        crawl_type = crawl_type or self.crawl_type
        handleKeyError(lst=SUPPORTED_CRAWL_TYPES, crawl_type=crawl_type)
        self.print(f"Crawling Type: {toACCENT(crawl_type)}")
        get_contents_func = getattr(self, f"get_contents_{crawl_type}")
        title, contents = get_contents_func(url=url, driver=driver, **gatewaykwargs)
        return (title, contents)

    def _get_contents_from_sections_base(self, sections):
        """Base method for ``get_contents_from_XXX``"""
        contents = []
        self.print(f"\nShow contents of the paper.\n{'='*30}")
        return contents

    # ================== #
    #  crawl_type="soup" #
    # ================== #

    @staticmethod
    def get_soup_url(url: str) -> str:
        """Convert the URL to the URL of the web page you access when ``crawl_type=="soup"``"""
        return url

    def get_contents_soup(
        self,
        url: Optional[str] = None,
        driver: Optional[WebDriver] = None,
        soup: Optional[BeautifulSoup] = None,
        **gatewaykwargs,
    ) -> Tuple[str, T_PAPER_CONTENT]:
        """Get contents from url of the web page using ``BeautifulSoup``.

        Args:
            url (str)            : URL of a paper.
            driver (WebDriver)   : Selenium WebDriver.
            gatewaykwargs (dict) : Gateway keywargs. See :meth:`passthrough <gummy.gateways.GummyAbstGateWay.passthrough>`.

        Returns:
            tuple (str, dict) : (title, content)
        """
        if soup is None:
            soup = self.get_soup_source(url=self.get_soup_url(url), driver=driver, **gatewaykwargs)
        else:
            soup = self.decompose_soup_tags(soup=soup)
        title = self.get_title_from_soup(soup)
        soup_sections = self.get_sections_from_soup(soup)
        contents = self.get_contents_from_soup_sections(soup_sections)
        self._store_crawling_logs(soup=soup, title=title, soup_sections=soup_sections, contents=contents)
        return (title, contents)

    def _get_soup_sections(
        self,
        url: Optional[str] = None,
        driver: Optional[WebDriver] = None,
        soup: Optional[BeautifulSoup] = None,
        **gatewaykwargs,
    ) -> Tuple[str, List[BeautifulSoup]]:
        """Utility functions for debugg."""
        if soup is None:
            soup = self.get_soup_source(url=self.get_soup_url(url), driver=driver, **gatewaykwargs)
        else:
            soup = self.decompose_soup_tags(soup=soup)
        title = self.get_title_from_soup(soup)
        soup_sections = self.get_sections_from_soup(soup)
        return (title, soup_sections)

    def get_soup_source(self, url: str, driver: Optional[WebDriver] = None, **gatewaykwargs) -> BeautifulSoup:
        """Scrape and get page source from ``url``.

        Args:
            url  (str)           : URL of a paper.
            driver (WebDriver)   : webdriver
            gatewaykwargs (dict) : Gateway keywargs. See :meth:`passthrough <gummy.gateways.GummyAbstGateWay.passthrough>`.

        Returns:
            BeautifulSoup : A data structure representing a parsed HTML or XML document.
        """
        # If url is None, we will use crawled information.
        cano_url = canonicalize(url=url, driver=driver)
        self._store_crawling_logs(cano_url=cano_url)
        # If driver is None, we could not use gateway service.
        if driver is None:
            html = requests.get(url=cano_url).content
            self.print(f"Get HTML content from {toBLUE(cano_url)}")
        else:
            driver, fmt_url_func = self.gateway.passthrough(
                driver=driver, url=cano_url, journal_type=self.journal_type, **gatewaykwargs
            )
            gateway_fmt_url = fmt_url_func(cano_url=cano_url)
            driver.get(gateway_fmt_url)
            self.print(f"Get HTML content from {toBLUE(gateway_fmt_url)}")
            wait_until_all_elements(driver=driver, timeout=self.sleep_for_loading, verbose=self.verbose)
            self.make_elements_visible(driver)
            html = driver.page_source.encode("utf-8")

        soup = BeautifulSoup(html, "html.parser")
        soup = self.decompose_soup_tags(soup=soup)
        return soup

    def make_elements_visible(self, driver: WebDriver) -> None:
        """Make all elements of the page visible.

        Args:
            driver (WebDriver)   : Selenium WebDriver.
        """
        scrollDown(driver=driver, verbose=self.verbose)

    def decompose_soup_tags(self, soup: BeautifulSoup) -> BeautifulSoup:
        """This function is not necessary for all Journals, but you can trim
        ``DecomposeSoupTags`` from the soup and it will help with debugging.

        Args:
            soup (BeautifulSoup) : A data structure representing a parsed HTML or XML document.

        Returns:
            tuple (BeautifulSoup, dict) : soup, a dict showing the number of decomposed tags.
        """
        self.print(f"\nDecompose unnecessary tags.\n{'='*30}")
        decoCounts = {}
        for decoKwargs in self.DecomposeSoupTags:
            decoTags = soup.find_all(**decoKwargs)
            self.print(f"Decomposed {len(decoTags)} {kwargs2tag(**decoKwargs)} tag{'s' if len(decoTags)!=1 else ''}.")
            for decoTag in decoTags:
                decoTag.decompose()
        return soup

    def register_decompose_soup_tags(self, **kwargs) -> None:
        """Register ``DecomposeSoupTags``

        Args:
            \*\*kwargs : Kwargs for ``soup.find`` method.
        """
        self.DecomposeSoupTags.append(kwargs)

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        """Get page title from page source.

        Args:
            soup (BeautifulSoup) : A data structure representing a parsed HTML or XML document.)

        Returns:
            str : A page title.
        """
        title = find_target_text(soup=soup, name="h1", default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        """Get sections from page source.

        Args:
            soup (BeautifulSoup) : A data structure representing a parsed HTML or XML document.)

        Returns:
            list : Page sections. Each element is (bs4.element.Tag)
        """
        sections = soup.find_all("section")
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        """Get head from a page section.

        Args:
            section (bs4.element.Tag) : Represents an HTML or XML tag that is part of a parse tree, along with its attributes and contents.

        Returns:
            bs4.element.Tag : A section head tag.
        """
        head = section.find(name="h2")
        return head

    def get_contents_from_soup_sections(self, soup_sections: List[BeautifulSoup]) -> List[T_PAPER_CONTENT]:
        """Get contents from each soup section.

        Args:
            soup_sections (list) : Each element is (bs4.element.Tag).

        Returns:
            list : Each element is ``dict`` (key is one of the ``["raw", "head", "subhead", "img"]``).
        """
        contents = self._get_contents_from_sections_base(soup_sections)
        len_soup_sections = len(soup_sections)
        for i, section in enumerate(soup_sections):
            headTag = self.get_head_from_section(section)
            if headTag is not None:
                head = str_strip(headTag.get_text())
                headTag.decompose()
            else:
                head = ""
            contents.extend(self.organize_soup_section(section=section, head=head, head_is_not_added=True))
            self.print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {head}")
        return contents

    def organize_soup_section(
        self, section: BeautifulSoup, head: str = "", head_is_not_added: bool = True
    ) -> List[T_PAPER_CONTENT]:
        """Organize soup section:

        - Extract an image and display it as ``base64`` format in the section.
        - Add ``head`` only to the initial content.

        Args:
            section (bs4.element.Tag) : Represents an HTML or XML tag that is part of a parse tree, along with its attributes and contents.
            head (str)                : Head word.
            head_is_not_added (bool)  : Whether head is added or not. (default= ``True``)
        """
        contents: List[T_PAPER_CONTENT] = []
        splitted_soup = split_section(
            section=section,
            name=lambda tag: tag.name == "img"
            or self.isSubheadTags(tag)
            or self.isSubSection(tag)
            or self.isFigCaption(tag),
        )
        for element in splitted_soup:
            content: T_PAPER_CONTENT = {}
            # <--- Add Head ---
            if head_is_not_added:
                content["head"] = head
                head_is_not_added = False
            # --- END Add Head -->

            # <--- Perform Processing According to the Element ---
            has_content: bool = True
            if element.name == "img":
                content["img"] = dict(src=src2base64(base=self.crawling_logs.get("cano_url"), src=element))
            elif self.isFigCaption(element) and len(contents) > 0 and ("img" in contents[-1]):
                contents[-1]["img"]["caption"] = dict(raw=self.arrange_english(str_strip(element.get_text())))
            elif self.isSubheadTags(element):
                content["subhead"] = str_strip(element.get_text())
            else:
                text: str = str_strip(element.get_text())
                if len(text) > 0:
                    content["body"] = dict(raw=self.arrange_english(text))
                elif not (("head" in content) and (len(content["head"]) > 0)):
                    has_content = False
            # --- END Perform Processing According to the Element --->

            if has_content:
                contents.append(content)
        return contents

    @staticmethod
    def arrange_english(english: str) -> str:
        """Get rid of extra characters from body (english). This method is used in :meth:`arrange_english <gummy.gateways.GummyAbstGateWay.organize_soup_section>`.

        Args:
            english (str) : Raw English.

        Returns:
            str : Arranged English
        """
        return english

    # ================== #
    #  crawl_type="tex"  #
    # ================== #

    @staticmethod
    def get_tex_url(url: str) -> str:
        """Convert the URL to the URL of the tex page you access when ``crawl_type=="tex"``"""
        return url

    def get_contents_tex(self, url: str, driver: Optional[WebDriver] = None) -> T_PAPER_TITLE_CONTENTS:
        """Get contents from url by parsing TeX sources.

        Args:
            url                  : (str) URL of a paper.
            driver               : (WebDriver) webdriver
            gatewaykwargs (dict) : Gateway keywargs. See :meth:`passthrough <gummy.gateways.GummyAbstGateWay.passthrough>`.

        Returns:
            tuple (str, dict) : (title, content)
        """
        tex = self.get_tex_source(url=self.get_tex_url(url), driver=driver)
        title = self.get_title_from_tex(tex)
        # NOTE: If we can scrape "title" from soup, please prioritize it.
        if self.get_pdf_url(url) != self.get_soup_url(url):
            soup = self.get_soup_source(url=self.get_soup_url(url), driver=None)
            title = self.get_title_from_soup(soup)
        tex_sections = self.get_sections_from_tex(tex)
        contents = self.get_contents_from_tex_sections(tex_sections)
        self._store_crawling_logs(tex=tex, title=title, tex_sections=tex_sections, contents=contents)
        return (title, contents)

    def get_tex_source(self, url: str, driver: Optional[WebDriver] = None) -> str:
        """Download and get tex source from url.

        Args:
            url (str)            : URL of a tex source or ``path/to/local.tex``.
            driver (WebDriver)   : Selenium WebDriver.

        Returns:
            str : Plain text in tex source.
        """
        if not os.path.exists(url):
            path = download_file(url=url, dirname=GUMMY_DIR)
            ext = "." + path.split(".")[-1]
            if is_compressed(ext):
                extracted_file_paths = extract_from_compressed(path, ext=".tex", dirname=GUMMY_DIR)
                path = extracted_file_paths[0]
        else:
            path = url
        with open(path, mode="r") as ftex:
            tex = LatexNodes2Text().latex_to_text(ftex.read())
        for decompose in self.DecomposeTexTags:
            tex = tex.replace(decompose, "")
        tex = re.sub("[ 　]+", " ", tex)
        return tex

    def get_title_from_tex(self, tex: str) -> str:
        """Get a title from tex source.

        Args:
            tex (str) : Plain text in tex source.

        Returns:
            str : TeX title.
        """
        title = "title"
        return title

    def get_sections_from_tex(self, tex: str) -> List[str]:
        """Get sections from tex source.

        Args:
            tex (str) : Plain text in tex source.

        Returns:
            list: Each element is plain text (str)
        """
        sections = [tex]
        return sections

    def get_contents_from_tex_sections(self, tex_sections: List[str]) -> List[T_PAPER_CONTENT]:
        """Get text for each tex section.

        Args:
            tex_sections : (list) Each element is plain text (str).

        Returns:
            (list) : Each element is ``dict`` (key is one of the ``["raw", "head", "subhead", "img"]``).
        """
        contents = self._get_contents_from_sections_base(tex_sections)
        len_tex_sections = len(tex_sections)
        for i, section in enumerate(tex_sections):
            content = {}
            first_nl = section.index("\n")
            head = str_strip(section[:first_nl])
            content["head"] = head
            content["body"] = dict(raw=section[first_nl:].replace("\n", ""))
            contents.append(content)
            self.print(f"[{i+1:>0{len(str(len_tex_sections))}}/{len_tex_sections}] {head}")
        return contents

    # ================== #
    #  crawl_type="pdf"  #
    # ================== #

    @staticmethod
    def get_pdf_url(url: str) -> str:
        """Convert the URL to the URL of the PDF page you access when ``crawl_type=="pdf"``"""
        return url

    def get_contents_pdf(self, url: str, driver: Optional[WebDriver] = None) -> T_PAPER_TITLE_CONTENTS:
        """Get contents from url by parsing PDF file.

        Args:
            url (str)            : URL of a paper or ``path/to/local.pdf``.
            driver (WebDriver)   : Selenium WebDriver.
            gatewaykwargs (dict) : Gateway keywargs. See :meth:`passthrough <gummy.gateways.GummyAbstGateWay.passthrough>`.

        Returns:
            tuple (str, dict) : (title, content)
        """
        pdf_pages = self.get_pdf_source(url=self.get_pdf_url(url), driver=driver)
        title = self.get_title_from_pdf(pdf_pages)
        # NOTE: If we can scrape "title" from soup, please prioritize it.
        if self.get_pdf_url(url) != self.get_soup_url(url):
            soup = self.get_soup_source(url=self.get_soup_url(url), driver=None)
            title = self.get_title_from_soup(soup)
        contents = self.get_contents_from_pdf_pages(pdf_pages)
        self._store_crawling_logs(title=title, pdf_pages=pdf_pages, contents=contents)
        return (title, contents)

    def get_pdf_source(self, url: str, driver: Optional[WebDriver] = None) -> List[Tuple[str, LTItem]]:
        """Download and get PDF source from url.

        Args:
            url (str)            : URL of a PDF file or ``path/to/local.pdf``.
            driver (WebDriver)   : Selenium WebDriver.

        Returns:
            list : Each element is a list which contains [text, bbox(x0,y0,x1,y1)]
        """
        pdf_pages = get_pdf_contents(file=url)
        return pdf_pages

    def get_title_from_pdf(self, pdf_pages: List[Tuple[str, LTItem]]) -> str:
        """Get title from PDF source.

        Args:
            pdf_pages (list) : Each element is a list which contains [text, bbox(x0,y0,x1,y1)]

        Returns:
            str : PDF title.
        """
        title = "title"
        return title

    def get_contents_from_pdf_pages(self, pdf_pages: List[Tuple[str, LTItem]]) -> Tuple[str, T_PAPER_CONTENT]:
        """Get contents from each page.

        Args:
            pdf_pages (list) : Each element is a list which contains [text, bbox(x0,y0,x1,y1)]

        Returns:
            tuple (str, dict) : (title, content)
        """
        contents = []
        len_pdf_pages = len(pdf_pages)
        digit = len(str(len_pdf_pages))
        for i, page_texts in enumerate(pdf_pages):
            page_no = f"Page.{i+1:>0{digit}}/{len_pdf_pages}"
            header = {"head": page_no, "raw": "", "bbox": (0, 0, 1, 1)}
            contents.append(header)
            for text, bbox in page_texts:
                content = {"raw": "", "bbox": bbox}
                if text.startswith('<img src="data:image/jpeg;base64'):
                    content["img"] = text
                else:
                    content["body"] = dict(raw=text.replace("-\n", "").replace("\n", " "))
                contents.append(content)
            self.print(page_no)
        return contents


class PDFCrawler(GummyAbstJournal):
    def __init__(self, gateway: str = "useless", sleep_for_loading: int = 3, verbose: bool = True, **kwargs):
        super().__init__(
            crawl_type="pdf",
            gateway="useless",
            sleep_for_loading=3,
        )

    @staticmethod
    def get_soup_url(url: str) -> str:
        return url

    @staticmethod
    def get_pdf_url(url: str) -> str:
        return url

    def get_contents_pdf(self, url: str, driver: Optional[WebDriver] = None) -> T_PAPER_TITLE_CONTENTS:
        _, contents = super().get_contents_pdf(url=url, driver=driver)
        if hasattr(url, "filename"):
            url = getattr(url, "filename")
        title = str(url).split("/")[-1].rstrip(".pdf")
        return title, contents


class NatureCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.nature.com

    Attributes:
        crawl_type (str)      : :meth:`NatureCrawler's <gummy.journals.NatureCrawler>` default ``crawl_type`` is ``"soup"``.
        AvoidAriaLabel (list) : Markers indicating the extra section to remove in :meth:`get_sections_from_soup <gummy.journals.NatureCrawler.get_sections_from_soup>`
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h3",
            isSubSection=lambda tag: tag.name == "p"
            and not ("c-article-section__figure-description" in tag.parent.get("class", [])),
            isFigCaption=lambda tag: tag.name == "div"
            and ("c-article-section__figure-description" in tag.get("class", [])),
        )
        self.register_decompose_soup_tags(name=lambda tag: tag.name == "sup" and tag.find(name="a") is not None)
        self.register_decompose_soup_tags(name="a", class_="c-article__pill-button")
        self.register_decompose_soup_tags(name="button")
        # References
        self.register_decompose_soup_tags(name="div", attrs=dict(id="MagazineFulltextArticleBodySuffix"))
        self.register_decompose_soup_tags(name="div", attrs=dict(id="Bib1-section"))
        # Acknowledgements
        self.register_decompose_soup_tags(name="div", attrs=dict(id="Ack1-section"))
        # Author information
        self.register_decompose_soup_tags(name="div", attrs=dict(id="author-information-section"))
        # Ethics declarations
        self.register_decompose_soup_tags(name="div", attrs=dict(id="ethics-section"))
        # Additional information
        self.register_decompose_soup_tags(name="div", attrs=dict(id="additional-information-section"))
        # Rights and permissions
        self.register_decompose_soup_tags(name="div", attrs=dict(id="rightslink-section"))
        # About this article
        self.register_decompose_soup_tags(name="div", attrs=dict(id="article-info"))
        # Further reading
        self.register_decompose_soup_tags(name="div", attrs=dict(id="further-reading-section"))
        # Other ways to remove the unnerecessary sections.
        self.AvoidAriaLabel: List[str] = [
            "Ack1",
            "Bib1",
            "additional-information",
            "article-comments",
            "article-info",
            "author-information",
            "ethics",
            "further-reading",
            "rightslink",
        ]  # ,None]

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="h1", attrs={"class": "c-article-title"}, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections: List[BeautifulSoup] = [
            e for e in soup.find_all(name="section") if e.get("aria-labelledby") not in self.AvoidAriaLabel
        ]
        # If the paper is old version, it may not be possible to obtain the content by the above way.
        if len(sections) == 0:
            sections = soup.find_all(name="div", class_="c-article-section__content")
        # sections = flatten_dual([e.find_all(name=("p", "h2")) for e in sections])
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class arXivCrawler(GummyAbstJournal):
    """
    URL:
        - https://arxiv.org

    Attributes:
        crawl_type (str)      : :meth:`arXivCrawler's <gummy.journals.arXivCrawler>` default ``crawl_type`` is ``"pdf"``.
        AvoidAriaLabel (list) : Markers indicating the extra section to remove in :meth:`get_sections_from_pdf <gummy.journals.arXivCrawler.get_sections_from_pdf>`
    """

    def __init__(self, sleep_for_loading=3, verbose=True, **kwargs):
        super().__init__(
            crawl_type="pdf",
            gateway="useless",
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            DecomposeTexTags=["<cit.>", "\xa0", "<ref>"],
        )
        self.AvoidAriaLabel = [
            None,
            "Bib1",
            "additional-information",
            "article-comments",
            "article-info",
            "author-information",
            "ethics",
            "further-reading",
            "rightslink",
        ]

    @staticmethod
    def get_pdf_url(url: str) -> str:
        return f"https://arxiv.org/pdf/{arXivCrawler.get_arXivNo(url)}.pdf"

    @staticmethod
    def get_soup_url(url: str) -> str:
        return f"https://arxiv.org/abs/{arXivCrawler.get_arXivNo(url)}"

    @staticmethod
    def get_tex_url(url: str) -> str:
        return f"https://arxiv.org/e-print/{arXivCrawler.get_arXivNo(url)}"

    @staticmethod
    def get_arXivNo(url: str) -> str:
        return re.sub(pattern=r"^.+\/((?:\d|\.|v)+)(?:\.pdf)?$", repl=r"\1", string=url)

    def get_sections_from_tex(self, tex: str) -> str:
        sections = tex.replace("§.§", "§").split("§")
        return sections

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", attrs={"class": "title mathjax"}, default=self.default_title
        ).lstrip("Title:")
        return title


class NCBICrawler(GummyAbstJournal):
    """
    URL:
        - https://www.ncbi.nlm.nih.gov

    Attributes:
        crawl_type (str) : :meth:`NCBICrawler's <gummy.journals.NCBICrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h3",
            isSubSection=lambda tag: tag.name == "p"
            and not (tag.parent.name == "div" and ("caption" in tag.parent.get("class", []))),
            isFigCaption=lambda tag: tag.name == "div" and ("icnblk_cntnt" in tag.get("class", [])),
        )
        self.register_decompose_soup_tags(name="a", text="Open in a separate window")
        self.register_decompose_soup_tags(name="div", class_="largeobj-link align_right")

    @staticmethod
    def arrange_english(english: str) -> str:
        return english[6:] if english.startswith("Go to:") else english

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="h1", class_="content-title", default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = [
            e
            for e in soup.find_all(name="div", class_="tsec")
            if (not e.get("id", "").startswith("ref-list"))
            or (not find_target_text(soup=e, name="h2", default="OK").lower().startswith("reference"))
        ]
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")  # , class_="c-article-section__title")
        return head


class PubMedCrawler(GummyAbstJournal):
    """
    URL:
        - https://pubmed.ncbi.nlm.nih.gov

    Attributes:
        crawl_type (str)        : :meth:`PubMedCrawler's <gummy.journals.PubMedCrawler>` default ``crawl_type`` is ``"soup"``.
        AvoidIdsPatterns (list) : Markers indicating the extra section to remove in :meth:`get_sections_from_soup <gummy.journals.PubMedCrawler.get_sections_from_soup>`
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )
        self.AvoidIdsPatterns = [r"^idm[0-9]+", r"^S49$", r"^ass-data$"]

    def get_contents_soup(self, url, driver=None, **gatewaykwargs):
        soup = self.get_soup_source(url=url, driver=driver, **gatewaykwargs)
        a_doi = soup.find(name="a", class_="id-link")
        if a_doi is not None:
            cano_url = canonicalize(url=a_doi.get("href"), driver=driver, sleep_for_loading=5)
            if cano_url != url:
                try:
                    journal_type = whichJournal(url=cano_url, driver=None, verbose=self.verbose)
                    if journal_type != "pubmed":  # Prevent infinite loop
                        crawler = get(journal_type, gateway=self.gateway, sleep_for_loading=3, verbose=self.verbose)
                        return crawler.get_contents(url=cano_url, driver=driver)
                except JournalTypeIndistinguishableError:
                    print(
                        f"{toGREEN('gummy.utils.journal_utils.whichJournal')} could not distinguish the journal type, so Scraping from PubMed"
                    )
        title = self.get_title_from_soup(soup)
        soup_sections = self.get_sections_from_soup(soup)
        contents = self.get_contents_from_soup_sections(soup_sections)
        self._store_crawling_logs(soup=soup, title=title, soup_sections=soup_sections, contents=contents)
        return (title, contents)

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="h1", class_="heading-title", strip=True, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", class_="abstract")
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2", class_="title")
        return head


class OxfordAcademicCrawler(GummyAbstJournal):
    """
    URL:
        - https://academic.oup.com

    Attributes:
        crawl_type (str) : :meth:`OxfordAcademicCrawler's <gummy.journals.OxfordAcademicCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name in ["h3", "h4"],
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", class_="article-title-main", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = []
        article_full_text = soup.find(name="div", class_="widget-items", attrs={"data-widgetname": "ArticleFulltext"})
        if article_full_text is not None:
            sections.extend(group_soup_with_head(soup=article_full_text, name="h2"))
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class ScienceDirectCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.sciencedirect.com

    Attributes:
        crawl_type (str) : :meth:`ScienceDirectCrawler's <gummy.journals.ScienceDirectCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h3",
        )
        self.register_decompose_soup_tags(name="ol", class_="links-for-figure")

    @staticmethod
    def get_soup_url(url: str) -> str:
        return url.replace("/abs/", "/")

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="span", class_="title-text", strip=True, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", class_="Abstracts")
        body = soup.find(name="div", attrs={"id": "body"})
        if body is not None:
            sections.extend(body.find_all(name="section"))
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class SpringerCrawler(GummyAbstJournal):
    """
    URL:
        - https://link.springer.com

    Attributes:
        crawl_type (str)      : :meth:`SpringerCrawler's <gummy.journals.SpringerCrawler>` default ``crawl_type`` is ``"soup"``.
        AvoidAriaLabel (list) : Markers indicating the extra section to remove in :meth:`get_sections_from_soup <gummy.journals.SpringerCrawler.get_sections_from_soup>`
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )
        self.AvoidAriaLabel = [
            None,
            "Ack1",
            "Bib1",
            "additional-information",
            "article-comments",
            "article-info",
            "author-information",
            "ethics",
            "further-reading",
            "rightslink",
        ]

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", class_="c-article-title", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = [e for e in soup.find_all(name="section") if e.get("aria-labelledby") not in self.AvoidAriaLabel]
        if len(sections) == 0:
            sections = [e for e in soup.find_all(name="section") if e.get("Abs1") not in self.AvoidAriaLabel]
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")  # , class_="c-article-section__title")
        return head


class MDPICrawler(GummyAbstJournal):
    """
    URL:
        - https://www.mdpi.com

    Attributes:
        crawl_type (str)      : :meth:`MDPICrawler's <gummy.journals.MDPICrawler>` default ``crawl_type`` is ``"soup"``.
        AvoidAriaLabel (list) : Markers indicating the extra section to remove in :meth:`get_sections_from_soup <gummy.journals.MDPICrawler.get_sections_from_soup>`
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h4",
        )
        self.AvoidAriaLabel = [
            None,
            "Ack1",
            "Bib1",
            "additional-information",
            "article-comments",
            "article-info",
            "author-information",
            "ethics",
            "further-reading",
            "rightslink",
        ]

    def get_soup_source(self, url: str, driver: Optional[WebDriver] = None, **gatewaykwargs):
        # If url is None, we will use crawled information.
        cano_url = canonicalize(url=url, driver=driver)
        cano_url = cano_url.rstrip("/htm") + "/htm"
        soup = super().get_soup_source(url=cano_url, driver=driver, **gatewaykwargs)
        return soup

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="h1", class_="title", strip=True, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="section", attrs={"type": "other"})
        sections = [e for e in soup.find_all(name="section") if e.get("aria-labelledby") not in self.AvoidAriaLabel]
        abst = soup.find(name="div", class_="art-abstract")
        if abst is not None:
            abst_section = soup.new_tag(name="section", attrs={"type": "other"})
            abst_h2Tag = soup.new_tag(name="h2")
            abst_h2Tag.string = "0. Abstract"
            abst_section.append(abst_h2Tag)
            abst_section.append(abst)
            sections.insert(0, abst_section)
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class UniOKLAHOMACrawler(GummyAbstJournal):
    """
    URL:
        - https://www.ou.edu

    Attributes:
        crawl_type (str) : :meth:`UniOKLAHOMACrawler's <gummy.journals.UniOKLAHOMACrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        sections = soup.find_all(name="p", class_="a")
        if len(sections) > 2:
            title = sections[1].get_text()
        else:
            title = self.default_title
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="p", class_=("a", "a0", "MsoNormal"))[2:]
        return sections

    def get_contents_from_soup_sections(self, soup_sections: List[BeautifulSoup]) -> List[T_PAPER_CONTENT]:
        contents = super()._get_contents_from_sections_base(soup_sections)
        len_soup_sections = len(soup_sections)
        for i, section in enumerate(soup_sections):
            contents.extend(self.organize_soup_section(section=section, head="", head_is_not_added=False))
            self.print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}]")
        return contents


class LungCancerCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.lungcancerjournal.info

    Attributes:
        crawl_type (str) : :meth:`LungCancerCrawler's <gummy.journals.LungCancerCrawler>` default ``crawl_type`` is ``"soup"``.
        AvoidHead (list) : Markers indicating the extra section to remove in :meth:`get_sections_from_soup <gummy.journals.LungCancerCrawler.get_sections_from_soup>`
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h3",
        )
        self.AvoidHead = [
            "",
            "Keywords",
            "References",
            "Article Info",
            "Publication History",
            "Identification",
            "Copyright",
            "ScienceDirect",
        ]

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", class_="article-header__title", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = [
            e
            for e in soup.find_all(name="section")
            if find_target_text(soup=e, name=("h2", "h3"), default="") not in self.AvoidHead
        ]
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class CellPressCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.cell.com

    Attributes:
        crawl_type (str)             : :meth:`CellPressCrawler's <gummy.journals.CellPressCrawler>` default ``crawl_type`` is ``"soup"``.
        AvoidDataLeftHandNavs (list) : Markers indicating the extra section to remove in :meth:`get_sections_from_soup <gummy.journals.CellPressCrawler.get_sections_from_soup>`
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h3",
        )
        self.AvoidDataLeftHandNavs = [None, "Acknowledgements", "References"]
        self.register_decompose_soup_tags(name="div", class_="dropBlock reference-citations")

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", class_="article-header__title", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = [
            e
            for e in soup.find_all(name="section")
            if find_target_id(soup=e, key="data-left-hand-nav", name="h2", default=None)
            not in self.AvoidDataLeftHandNavs
        ]
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class WileyOnlineLibraryCrawler(GummyAbstJournal):
    """
    URL:
        - https://agupubs.onlinelibrary.wiley.com
        - https://anatomypubs.onlinelibrary.wiley.com
        - https://besjournals.onlinelibrary.wiley.com
        - https://febs.onlinelibrary.wiley.com
        - https://onlinelibrary.wiley.com
        - https://stemcellsjournals.onlinelibrary.wiley.com

    Attributes:
        crawl_type (str) : :meth:`WileyOnlineLibraryCrawler's <gummy.journals.WileyOnlineLibraryCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name in ["h3", "h4"],
        )
        self.register_decompose_soup_tags(name="a")

    @staticmethod
    def get_soup_url(url: str) -> str:
        # return re.sub(pattern=r"\/(?:abs|pdf)\/", repl="/full/", string=url)
        return re.sub(
            pattern=r"\/doi(?:\/(full|e?pdf))?\/",
            repl=lambda m: m.group(0).replace(m.group(1), "full")
            if m.group(1) is not None
            else m.group(0).replace("/doi/", "/doi/full/"),
            string=url,
        )

    @staticmethod
    def get_pdf_url(url: str) -> str:
        # return re.sub(pattern=r"\/(?:abs|full)\/", repl="/pdf/", string=url)
        return re.sub(
            pattern=r"\/doi(?:\/(full|e?pdf))?\/",
            repl=lambda m: m.group(0).replace(m.group(1), "pdf")
            if m.group(1) is not None
            else m.group(0).replace("/doi/", "/doi/pdf/"),
            string=url,
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", class_="citation__title", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="section", class_=("article-section__abstract", "article-section__content"))
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class JBCCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.jbc.org

    Attributes:
        crawl_type (str) : :meth:`JBCCrawler's <gummy.journals.JBCCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h3",
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", attrs={"id": "article-title-1"}, strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", class_=("section abstract"))
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class BiologistsCrawler(GummyAbstJournal):
    """
    URL:
        - https://bio.biologists.org
        - https://dev.biologists.org
        - https://jcs.biologists.org

    Attributes:
        crawl_type (str) : :meth:`BiologistsCrawler's <gummy.journals.BiologistsCrawler>` default ``crawl_type`` is ``"soup"``.
        AvoidIDs (list)  : Markers indicating the extra section to remove in :meth:`get_sections_from_soup <gummy.journals.BiologistsCrawler.get_sections_from_soup>`
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h3",
        )
        self.AvoidIDs = ["ack", "fn-group", "ref-list"]

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="div", class_="highwire-cite-title", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = [
            e
            for e in soup.find_all(name="div", class_="section")
            if not any([e.get("id", self.AvoidIDs[0]).startswith(id) for id in self.AvoidIDs])
        ]
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class BioMedCentralCrawler(GummyAbstJournal):
    """
    URL:
        - https://biologydirect.biomedcentral.com
        - https://bmcbioinformatics.biomedcentral.com
        - https://bmcevolbiol.biomedcentral.com
        - https://bmcgenomics.biomedcentral.com
        - https://genomebiology.biomedcentral.com
        - https://retrovirology.biomedcentral.com

    Attributes:
        crawl_type (str)      : :meth:`BioMedCentralCrawler's <gummy.journals.BioMedCentralCrawler>` default ``crawl_type`` is ``"soup"``.
        AvoidAriaLabel (list) : Markers indicating the extra section to remove in :meth:`get_sections_from_soup <gummy.journals.BioMedCentralCrawler.get_sections_from_soup>`
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h3",
        )
        self.AvoidAriaLabel = [
            "Ack1",
            "Bib1",
            "additional-information",
            "article-comments",
            "article-info",
            "author-information",
            "ethics",
            "further-reading",
            "rightslink",
            "Sec2",
            "Sec3",
        ]  # ,None]

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", class_="c-article-title", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = [e for e in soup.find_all(name="section") if e.get("aria-labelledby") not in self.AvoidAriaLabel]
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class IEEEXploreCrawler(GummyAbstJournal):
    """
    URL:
        - https://ieeexplore.ieee.org

    Attributes:
        crawl_type (str) : :meth:`IEEEXploreCrawler's <gummy.journals.IEEEXploreCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(self, gateway="useless", sleep_for_loading=10, verbose=True, **kwargs):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h3",
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="h1", class_="document-title", strip=True, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
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

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="div", class_="header")
        return head


class JSTAGECrawler(GummyAbstJournal):
    """
    URL:
        - https://www.jstage.jst.go.jp

    Attributes:
        crawl_type (str) : :meth:`JSTAGECrawler's <gummy.journals.JSTAGECrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    def get_soup_source(self, url: str, driver: Optional[WebDriver] = None, **gatewaykwargs):
        cano_url = canonicalize(url=url, driver=driver)
        self.print(f"You can download PDF from {toBLUE(cano_url.replace('_article', '_pdf/-char/en'))}")
        soup = super().get_soup_source(url=cano_url, driver=driver, **gatewaykwargs)
        return soup

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="div", class_="global-article-title", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", attrs={"id": "article-overiew-abstract-wrap"})
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="div")
        return head


class ACSPublicationsCrawler(GummyAbstJournal):
    """
    URL:
        - https://pubs.acs.org/

    Attributes:
        crawl_type (str) : :meth:`ACSPublicationsCrawler's <gummy.journals.ACSPublicationsCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name in ["h4", "h5", "h6"],
        )

    def get_soup_source(self, url: str, driver: Optional[WebDriver] = None, **gatewaykwargs):
        cano_url = canonicalize(url=url, driver=driver)
        self.print(f"You can download PDF from {toBLUE(cano_url.replace('/doi/', '/doi/pdf/'))}")
        soup = super().get_soup_source(url=cano_url, driver=driver, **gatewaykwargs)
        return soup

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", class_="article_header-title", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", class_=("article_abstract", "NLM_sec NLM_sec_level_1"))
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class UniKeioCrawler(GummyAbstJournal):
    """
    URL:
        - https://keio.pure.elsevier.com

    Attributes:
        crawl_type (str) : :meth:`UniKeioCrawler's <gummy.journals.UniKeioCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    def get_contents_soup(self, url, driver=None, **gatewaykwargs):
        soup = self.get_soup_source(url=url, driver=driver, **gatewaykwargs)
        div_doi = soup.find(name="div", class_="doi")
        if div_doi is not None:
            a_doi = div_doi.find(name="a")
            if a_doi is not None:
                cano_url = canonicalize(url=a_doi.get("href"), driver=driver, sleep_for_loading=5)
                if cano_url != url:
                    try:
                        journal_type = whichJournal(url=cano_url, driver=None, verbose=self.verbose)
                        if journal_type != "unikeio":  # Prevent infinite loop
                            crawler = get(
                                journal_type, gateway=self.gateway, sleep_for_loading=3, verbose=self.verbose
                            )
                            return crawler.get_contents(url=cano_url, driver=driver)
                    except JournalTypeIndistinguishableError:
                        print(
                            f"{toGREEN('gummy.utils.journal_utils.whichJournal')} could not distinguish the journal type, so Scraping from PubMed"
                        )
        title = self.get_title_from_soup(soup)
        soup_sections = self.get_sections_from_soup(soup)
        contents = self.get_contents_from_soup_sections(soup_sections)
        self._store_crawling_logs(soup=soup, title=title, soup_sections=soup_sections, contents=contents)
        return (title, contents)

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="h1", strip=True, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", class_="rendering_contributiontojournal_abstractportal")
        return sections

    def get_contents_from_soup_sections(self, soup_sections: List[BeautifulSoup]) -> List[T_PAPER_CONTENT]:
        contents = super()._get_contents_from_sections_base(soup_sections)
        len_soup_sections = len(soup_sections)
        for i, section in enumerate(soup_sections):
            head = section.get("class", ["Abstract"])[-1]
            contents.extend(self.organize_soup_section(section=section, head=head))
            self.print(f"[{i+1:>0{len(str(len_soup_sections))}}/{len_soup_sections}] {head}")
        return contents


class PLOSONECrawler(GummyAbstJournal):
    """
    URL:
        - https://journals.plos.org

    Attributes:
        crawl_type (str) : :meth:`PLOSONECrawler's <gummy.journals.PLOSONECrawler>` default ``crawl_type`` is ``"soup"``.
        AvoidIDs (list)  : Markers indicating the extra section to remove in :meth:`get_sections_from_soup <gummy.journals.PLOSONECrawler.get_sections_from_soup>`
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h3",
        )
        self.AvoidIDs = ["authcontrib", "references"]

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", attrs={"id": "artTitle"}, strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = [
            e
            for e in soup.find_all(name="div", class_="toc-section")
            if e.find(name="a") is not None and e.find(name="a").get("id") not in self.AvoidIDs
        ]
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class frontiersCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.frontiersin.org

    Attributes:
        crawl_type (str) : :meth:`frontiersCrawler's <gummy.journals.frontiersCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name in ["h2", "h3", "h4"],
        )
        self.register_decompose_soup_tags(name="div", class_="authors")
        self.register_decompose_soup_tags(name="ul", class_="notes")

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        abst = soup.find(name="div", class_="JournalAbstract")
        if abst is None:
            abst = soup
        title = find_target_text(soup=abst, name="h1", strip=True, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", class_="JournalAbstract")
        text_section = soup.find(name="div", class_="JournalFullText")
        if text_section is not None:
            sections.extend(group_soup_with_head(soup=text_section, name="h2"))
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h1")
        return head


class RNAjournalCrawler(GummyAbstJournal):
    """
    URL:
        - https://rnajournal.cshlp.org

    Attributes:
        crawl_type (str) : :meth:`RNAjournalCrawler's <gummy.journals.RNAjournalCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    def get_soup_source(self, url: str, driver: Optional[WebDriver] = None, **gatewaykwargs):
        cano_url = canonicalize(url=url, driver=driver)
        self.print(f"You can download PDF from {toBLUE(cano_url + '.full.pdf')}")
        soup = super().get_soup_source(url=cano_url, driver=driver, **gatewaykwargs)
        return soup

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup,
            name="h1",
            attrs={"id": "article-title-1", "itemprop": "headline"},
            strip=True,
            default=self.default_title,
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", class_="section")
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class IntechOpenCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.intechopen.com

    Attributes:
        crawl_type (str) : :meth:`IntechOpenCrawler's <gummy.journals.IntechOpenCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h3",
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="h1", class_="title", strip=True, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", class_="intro")
        body = soup.find(name="div", class_="reader-body")
        if body is not None:
            sections.extend(body.find_all(name="div", class_="section"))
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class NRCResearchPressCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.nrcresearchpress.com

    Attributes:
        crawl_type (str) : :meth:`NRCResearchPressCrawler's <gummy.journals.NRCResearchPressCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "span" and ("title2" in tag.get("class", [])),
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="h1", class_="article-title", strip=True, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", class_="box-pad border-lightgray margin-bottom")
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class SpandidosCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.spandidos-publications.com

    Attributes:
        crawl_type (str) : :meth:`SpandidosCrawler's <gummy.journals.SpandidosCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h5",
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="h1", attrs={"id": "titleId"}, strip=True, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", attrs={"id": "articleAbstract"})
        try:
            sections.extend(group_soup_with_head(soup=sections[0].next.next.next, name=("h4", "h5")))
        except AttributeError:
            print("Use only Abstract.")
        except IndexError:
            print(toRED("Couldn't scrape well."))
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h4")
        return head


class TaylorandFrancisOnlineCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.tandfonline.com

    Attributes:
        crawl_type (str) : :meth:`TaylorandFrancisOnlineCrawler's <gummy.journals.TaylorandFrancisOnlineCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h3",
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="h1", attrs={"id": "titleId"}, strip=True, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", class_=("hlFld-Abstract", "NLM_sec NLM_sec-type_intro NLM_sec_level_1"))
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class bioRxivCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.biorxiv.org

    Attributes:
        crawl_type (str) : :meth:`bioRxivCrawler's <gummy.journals.bioRxivCrawler>` default ``crawl_type`` is ``"soup"``.
        AvoidIDs (list)  : Markers indicating the extra section to remove in :meth:`get_sections_from_soup <gummy.journals.bioRxivCrawler.get_sections_from_soup>`
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h3",
        )
        self.AvoidIDs = ["ref-list-1"]

    @staticmethod
    def get_soup_url(url: str) -> str:
        return re.sub(pattern=r"(.+?)(:?\.full)?", string=url, repl=r"\1") + ".full"

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup,
            name="h1",
            attrs={"id": "page-title", "class": "highwire-cite-title"},
            strip=True,
            default=self.default_title,
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", class_="article fulltext-view")
        if len(sections) > 0:
            sections = [
                e for e in sections[0].find_all(name="div", class_="section") if e.get("id") not in self.AvoidIDs
            ]
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class RSCPublishingCrawler(GummyAbstJournal):
    """
    URL:
        - https://pubs.rsc.org

    Attributes:
        crawl_type (str) : :meth:`RSCPublishingCrawler's <gummy.journals.RSCPublishingCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="h2", class_="capsule__title", strip=True, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", class_="capsule__column-wrapper")
        text_section = soup.find(name="div", attrs={"id": "pnlArticleContent"})
        if text_section is not None:
            sections.extend(group_soup_with_head(soup=text_section, name="h2"))
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class JSSECrawler(GummyAbstJournal):
    """
    URL:
        - https://www.jsse.org

    Attributes:
        crawl_type (str) : :meth:`JSSECrawler's <gummy.journals.JSSECrawler>` default ``crawl_type`` is ``"pdf"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="pdf",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    @staticmethod
    def get_jsseNo(url):
        return re.sub(
            pattern=r"^.*\/index.php\/jsse\/article\/(?:view|download)\/([0-9]+)(?:\/[0-9]+)?$", repl=r"\1", string=url
        )

    @staticmethod
    def get_soup_url(url: str) -> str:
        return f"https://www.jsse.org/index.php/jsse/article/view/{JSSECrawler.get_jsseNo(url)}"

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="h1", class_="page_title", strip=True, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", class_="item abstract")
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h3")
        return head


class ScienceCrawler(GummyAbstJournal):
    """
    URL:
        - https://advances.sciencemag.org
        - https://science.sciencemag.org
        - https://www.science.org

    Attributes:
        crawl_type (str) : :meth:`ScienceCrawler's <gummy.journals.ScienceCrawler>` default ``crawl_type`` is ``"soup"``.
        AvoidIDs (list)  : Markers indicating the extra section to remove in :meth:`get_sections_from_soup <gummy.journals.ScienceCrawler.get_sections_from_soup>`
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h3",
        )
        self.AvoidIDs = ["ref-list-1"]

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", class_="article__headline", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections: List[BeautifulSoup] = []
        abstract: BeautifulSoup = soup.find(name="div", attrs={"id": "abstracts"})
        if abstract is not None:
            sections.append(abstract)

        article: BeautifulSoup = soup.find(name="section", attrs={"id": "bodymatter"})
        if article is not None:
            sections.extend(article.find_all(name="section"))
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class medRxivCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.medrxiv.org

    Attributes:
        crawl_type (str) : :meth:`medRxivCrawler's <gummy.journals.medRxivCrawler>` default ``crawl_type`` is ``"pdf"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="pdf",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    @staticmethod
    def get_soup_url(url: str) -> str:
        return re.sub(pattern=r"(^.*\/.*?v[0-9]+)(\..+)?", repl=r"\1", string=url)

    @staticmethod
    def get_pdf_url(url: str) -> str:
        return medRxivCrawler.get_soup_url(url) + ".full.pdf"

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup,
            name="h1",
            attrs={"class": "highwire-cite-title", "id": "page-title"},
            strip=True,
            default=self.default_title,
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", class_="section")
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class ACLAnthologyCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.aclweb.org

    Attributes:
        crawl_type (str) : :meth:`ACLAnthologyCrawler's <gummy.journals.ACLAnthologyCrawler>` default ``crawl_type`` is ``"pdf"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="pdf",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    @staticmethod
    def get_soup_url(url: str) -> str:
        return url.rstrip("/").rstrip(".pdf")

    @staticmethod
    def get_pdf_url(url: str) -> str:
        return ACLAnthologyCrawler.get_soup_url(url) + ".pdf"

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="h2", attrs={"id": "title"}, strip=True, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", class_="card-body acl-abstract")
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h5")
        return head


class PNASCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.pnas.org

    Attributes:
        crawl_type (str) : :meth:`PNASCrawler's <gummy.journals.PNASCrawler>` default ``crawl_type`` is ``"soup"``.
        AvoidIDs (list)  : Markers indicating the extra section to remove in :meth:`get_sections_from_soup <gummy.journals.PNASCrawler.get_sections_from_soup>`
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h3",
        )
        self.AvoidIDs = ["fn-group-1", "ref-list-1"]

    @staticmethod
    def get_soup_url(url: str) -> str:
        return url.rstrip("/").rstrip(".full.pdf")

    @staticmethod
    def get_pdf_url(url: str) -> str:
        return PNASCrawler.get_soup_url(url) + ".full.pdf"

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup,
            name="h1",
            attrs={"class": "highwire-cite-title", "id": "page-title"},
            strip=True,
            default=self.default_title,
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", class_="executive-summary")
        sections += [e for e in soup.find_all(name="div", class_="section") if e.get("id") not in self.AvoidIDs]
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class AMSCrawler(GummyAbstJournal):
    """
    URL:
        - https://journals.ametsoc.org

    Attributes:
        crawl_type (str) : :meth:`AMSCrawler's <gummy.journals.AMSCrawler>` default ``crawl_type`` is ``"soup"``.
        AvoidIDs (list)  : Markers indicating the extra section to remove in :meth:`get_sections_from_soup <gummy.journals.AMSCrawler.get_sections_from_soup>`
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h3",
        )
        self.AvoidIDs = ["fn-group-1", "ref-list-1"]

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", class_="wi-article-title article-title-main", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = []
        article = soup.find(name="div", attrs={"class": "widget-items", "data-widgetname": "ArticleFulltext"})
        if article is not None:
            head = article.find(name=("h2", "h3"))
            while head is not None:
                section = BeautifulSoup(features="lxml").new_tag(name="section")
                article = head.find_next_sibling(name=("div"))
                section.append(head)
                head = article.find_next_sibling(name=("h2", "h3"))
                if (
                    head is None
                    or head.get_text() == "REFERENCES"
                    or ("backreferences-title" in head.get("class", []))
                ):
                    break
                section.append(article)
                sections.append(section)
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class ACMCrawler(GummyAbstJournal):
    """NOTE: If you want to download PDF, you must run driver with a browser.

    URL:
        - https://dl.acm.org

    Attributes:
        crawl_type (str) : :meth:`ACMCrawler's <gummy.journals.ACMCrawler>` default ``crawl_type`` is ``"pdf"``.
        AvoidIDs (list)  : Markers indicating the extra section to remove in :meth:`get_sections_from_pdf <gummy.journals.ACMCrawler.get_sections_from_pdf>`
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="pdf",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )
        self.AvoidIDs = ["sec-ref", "sec-terms", "sec-comments"]

    @staticmethod
    def get_soup_url(url: str) -> str:
        return re.sub(
            pattern=r"\/doi(?:\/(abs|e?pdf))?\/",
            repl=lambda m: m.group(0).replace(m.group(1), "abs")
            if m.group(1) is not None
            else m.group(0).replace("/doi/", "/doi/abs/"),
            string=url,
        )

    @staticmethod
    def get_pdf_url(url: str) -> str:
        return re.sub(
            pattern=r"\/doi(?:\/(abs|e?pdf))?\/",
            repl=lambda m: m.group(0).replace(m.group(1), "pdf")
            if m.group(1) is not None
            else m.group(0).replace("/doi/", "/doi/pdf/"),
            string=url,
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", class_="citation__title", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = [
            e
            for e in soup.find_all(name="div", class_="article__section")
            if e.find("h2") is None or e.find("h2").get("id") not in self.AvoidIDs
        ]
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class APSCrawler(GummyAbstJournal):
    """
    URL:
        - https://journals.aps.org

    Attributes:
        crawl_type (str) : :meth:`APSCrawler's <gummy.journals.APSCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h6",
        )

    @staticmethod
    def get_soup_url(url: str) -> str:
        return url.replace("/pdf/", "/abstract/")

    @staticmethod
    def get_pdf_url(url: str) -> str:
        return url.replace("/abstract/", "/pdf/")

    def make_elements_visible(self, driver):
        driver.implicitly_wait(3)
        try_find_element_click(
            driver=driver,
            identifier="//section[@class='article fulltext']/h4[@class='title']/span[@class='right']/i[@class='fi-plus']",
            by="xpath",
        )
        while True:
            hidden_elements = driver.find_elements(
                by="xpath", value="//i[@class='fi-plus'][contains(@style,'display: block;')]"
            )
            for e in hidden_elements:
                try_find_element_click(driver=driver, target=e)
            if len(hidden_elements) == 0:
                break

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="h3", strip=True, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="section", class_="article-section")
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h5", class_="section title")
        return head


class ASIPCrawler(GummyAbstJournal):
    """
    URL:
        - https://ajp.amjpathol.org

    Attributes:
        crawl_type (str) : :meth:`ASIPCrawler's <gummy.journals.ASIPCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h3",
        )

    @staticmethod
    def get_asipID(url):
        return re.sub(
            pattern=r"^.+\/(?:(?:article\/(.+)\/)|(?:action\/showPdf\?pii=(.+))).*$",
            repl=lambda m: m.group(1) or m.group(2),
            string=url,
        )

    @staticmethod
    def get_soup_url(url: str) -> str:
        return f"https://ajp.amjpathol.org/article/{ASIPCrawler.get_asipID(url)}/fulltext"

    @staticmethod
    def get_pdf_url(url: str) -> str:
        return f"https://ajp.amjpathol.org/action/showPdf?pii={ASIPCrawler.get_asipID(url)}"

    def get_soup_source(self, url: str, driver: Optional[WebDriver] = None, **gatewaykwargs):
        asipID = self.get_asipID(url)
        soup = super().get_soup_source(url=self.get_soup_url(asipID), driver=driver, **gatewaykwargs)
        return soup

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", class_="article-header__title", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = []
        article = soup.find(name="div", class_="article__sections")
        if article is not None:
            for section in article.find_all(name="section"):
                if find_target_text(soup=section, name="h2", default="OK").lower().startswith("reference"):
                    break
                sections.append(section)
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class RenalPhysiologyCrawler(GummyAbstJournal):
    """
    URL:
        - https://journals.physiology.org

    Attributes:
        crawl_type (str) : :meth:`RenalPhysiologyCrawler's <gummy.journals.RenalPhysiologyCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h2",
        )

    @staticmethod
    def get_soup_url(url: str) -> str:
        return re.sub(
            pattern=r"\/doi(?:\/(full|e?pdf))?\/",
            repl=lambda m: m.group(0).replace(m.group(1), "full")
            if m.group(1) is not None
            else m.group(0).replace("/doi/", "/doi/full/"),
            string=url,
        )

    @staticmethod
    def get_pdf_url(url: str) -> str:
        return re.sub(
            pattern=r"\/doi(?:\/(full|e?pdf))?\/",
            repl=lambda m: m.group(0).replace(m.group(1), "pdf")
            if m.group(1) is not None
            else m.group(0).replace("/doi/", "/doi/pdf/"),
            string=url,
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", class_="citation__title", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", class_="hlFld-Abstract")
        body_section = soup.find(name="div", class_="hlFld-Fulltextl")
        if body_section is not None:
            sections.extend(group_soup_with_head(soup=body_section, name="h1"))
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h1")
        return head


class GeneticsCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.genetics.org

    Attributes:
        crawl_type (str) : :meth:`GeneticsCrawler's <gummy.journals.GeneticsCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h4",
        )

    @staticmethod
    def get_soup_url(url: str) -> str:
        return url.rstrip(".full.pdf").replace("/content/genetics/", "/content/")

    @staticmethod
    def get_pdf_url(url: str) -> str:
        return GeneticsCrawler.get_soup_url(url).replace("/content/", "/content/genetics/") + ".full.pdf"

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup,
            name="h1",
            attrs={"class": "highwire-cite-title", "id": "page-title"},
            strip=True,
            default=self.default_title,
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = []
        article = soup.find(name="div", class_="article fulltext-view")
        if article is not None:
            article_sections = group_soup_with_head(soup=article, name="h2")
            for article_section in article_sections:
                h2Tag = article_section.find(name="h2")
                if (h2Tag is not None) and h2Tag.get_text().lower().startswith("reference"):
                    break
                sections.append(article_section)
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class GeneDevCrawler(GummyAbstJournal):
    """
    URL:
        - https://genesdev.cshlp.org

    Attributes:
        crawl_type (str) : :meth:`GeneDevCrawler's <gummy.journals.GeneDevCrawler>` default ``crawl_type`` is ``"pdf"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="pdf",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    @staticmethod
    def get_soup_url(url: str) -> str:
        return url.rstrip("+html").rstrip(".full.pdf")

    @staticmethod
    def get_pdf_url(url: str) -> str:
        return GeneDevCrawler.get_soup_url(url) + ".full.pdf"

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup,
            name="h1",
            attrs={"id": "article-title-1", "itemprop": "headline"},
            strip=True,
            default=self.default_title,
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", class_="section abstract")
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class JAMANetworkCrawler(GummyAbstJournal):
    """
    URL:
        - https://jamanetwork.com

    Attributes:
        crawl_type (str) : :meth:`JAMANetworkCrawler's <gummy.journals.JAMANetworkCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "strong",
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", class_="meta-article-title", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = []
        article = soup.find(name="div", class_="article-full-text")
        if article is not None:
            article_sections = group_soup_with_head(soup=article, name="div", class_="h3")
            for article_section in article_sections:
                if article_section.find(name="div", class_="references") is not None:
                    break
                sections.append(article_section)
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="div", class_="h3")
        return head


class SAGEjournalsCrawler(GummyAbstJournal):
    """
    URL:
        - https://journals.sagepub.com

    Attributes:
        crawl_type (str) : :meth:`SAGEjournalsCrawler's <gummy.journals.SAGEjournalsCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="h1", strip=True, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", class_="hlFld-Abstract")
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class MolCellBioCrawler(GummyAbstJournal):
    """
    URL:
        - https://mcb.asm.org

    Attributes:
        crawl_type (str) : :meth:`MolCellBioCrawler's <gummy.journals.MolCellBioCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "span",
        )

    @staticmethod
    def get_soup_url(url: str) -> str:
        return url.rstrip(".full.pdf")

    @staticmethod
    def get_pdf_url(url: str) -> str:
        return MolCellBioCrawler.get_soup_url(url) + ".full.pdf"

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", class_="highwire-cite-title", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = []
        article = soup.find(name="div", class_="article fulltext-view")
        if article is not None:
            article_sections = group_soup_with_head(soup=article, name="h2")
            for article_section in article_sections:
                h2Tag = article_section.find(name="h2")
                if (h2Tag is not None) and h2Tag.get_text().lower().startswith("reference"):
                    break
                sections.append(article_section)
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class JKMSCrawler(GummyAbstJournal):
    """
    URL:
        - https://jkms.org

    Attributes:
        crawl_type (str) : :meth:`JKMSCrawler's <gummy.journals.JKMSCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    @staticmethod
    def get_pdf_url(url: str) -> str:
        if not url.endswith(".pdf"):
            soup = BeautifulSoup(requests.get(url=url).content, "html.parser")
            PDF_urls = [a.get("href") for a in soup.find_all(name="a") if a.get_text().upper() == "PDF"]
            if len(PDF_urls) > 0:
                url = PDF_urls[0]
        return url

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="span", class_="tl-document", strip=True, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", class_=("fm", "body"))
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="div", class_="tl-main-part")
        return head


class JKNSCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.jkns.or.kr

    Attributes:
        crawl_type (str) : :meth:`JKNSCrawler's <gummy.journals.JKNSCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    @staticmethod
    def get_pdf_url(url: str) -> str:
        if not url.endswith(".pdf"):
            soup = BeautifulSoup(requests.get(url=url).content, "html.parser")
            PDF_urls = [a.get("onclick") for a in soup.find_all(name="a") if a.get_text().strip() == "PDF Links"]
            if len(PDF_urls) > 0:
                url = re.sub(
                    pattern=r'journal_download\("(.+?)",\s*"(.+?)",\s*"(.+?)"\)',
                    repl=r"https://www.jkns.or.kr/upload/pdf/\3",
                    string=PDF_urls[0],
                )
        return url

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="h3", class_="PubTitle", strip=True, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", class_="abstract-layer")
        article = soup.find(name="div", class_="abstract-layer")
        if article is not None:
            sections.extend(article.find_all(name="div", class_="section"))
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h3")
        return head


class BioscienceCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.bioscience.org

    Attributes:
        crawl_type (str) : :meth:`BioscienceCrawler's <gummy.journals.BioscienceCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    @staticmethod
    def get_soup_url(url: str) -> str:
        soup = BeautifulSoup(requests.get(url=url).content, "html.parser")
        frame_urls = [
            e.get("src")
            for e in soup.find_all(name="frame")
            if re.search(pattern=r"\.html?", string=e.get("src")) is not None
        ]
        if len(frame_urls) > 0:
            url = re.sub(pattern=r"(^.*\/)(.+?\.html?)$", repl=r"\1", string=url) + frame_urls[0]
        return url

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="p", attrs={"align": "JUSTIFY"}, strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="p", attrs={"align": "JUSTIFY"})
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="b")
        return head


class RadioGraphicsCrawler(GummyAbstJournal):
    """
    URL:
        - https://pubs.rsna.org

    Attributes:
        crawl_type (str) : :meth:`RadioGraphicsCrawler's <gummy.journals.RadioGraphicsCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    @staticmethod
    def get_soup_url(url: str) -> str:
        return url.replace("/doi/pdf/", "/doi/")

    @staticmethod
    def get_pdf_url(url: str) -> str:
        return RadioGraphicsCrawler.get_soup_url(url).replace("/doi/", "/doi/pdf/")

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", class_="citation__title", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", class_="hlFld-Abstract")
        article = soup.find(name="div", class_="hlFld-Fulltext")
        if article is not None:
            sections.extend(
                group_soup_with_head(soup=article, name="h2", class_="article-section__title section__title")
            )
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class PediatricSurgeryCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.jpedsurg.org

    Attributes:
        crawl_type (str)             : :meth:`PediatricSurgeryCrawler's <gummy.journals.PediatricSurgeryCrawler>` default ``crawl_type`` is ``"soup"``.
        AvoidDataLeftHandNavs (list) : Markers indicating the extra section to remove in :meth:`get_sections_from_soup <gummy.journals.PediatricSurgeryCrawler.get_sections_from_soup>`
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )
        self.AvoidDataLeftHandNavs = [None, "References"]

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", class_="article-header__title", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = [
            e
            for e in soup.find_all(name="section")
            if (e.find(name="h2") is not None)
            and (e.find(name="h2").get("data-left-hand-nav") not in self.AvoidDataLeftHandNavs)
        ]
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class NEJMCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.nejm.org

    Attributes:
        crawl_type (str) : :meth:`NEJMCrawler's <gummy.journals.NEJMCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h2",
        )

    @staticmethod
    def get_soup_url(url: str) -> str:
        return url.replace("/pdf/", "/full/")

    @staticmethod
    def get_pdf_url(url: str) -> str:
        return url.replace("/full/", "/pdf/")

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="span", class_="title_default", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="section", class_="o-article-body__section")
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class LWWJournalsCrawler(GummyAbstJournal):
    """
    URL:
        - https://journals.lww.com

    Attributes:
        crawl_type (str) : :meth:`LWWJournalsCrawler's <gummy.journals.LWWJournalsCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h3",
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="header", class_="ejp-article-header", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="section", attrs={"id": "abstractWrap"})
        article = soup.find(name="section", attrs={"id": "ArticleBody"})
        if article is not None:
            sections.extend(group_soup_with_head(soup=article, name="h2"))
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name=("h1", "h2"))
        return head


class ARVOJournalsCrawler(GummyAbstJournal):
    """
    URL:
        - https://iovs.arvojournals.org/
        - https://jov.arvojournals.org/
        - https://tvst.arvojournals.org/

    Attributes:
        crawl_type (str) : :meth:`ARVOJournalsCrawler's <gummy.journals.ARVOJournalsCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "strong",
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="div", class_="wi-article-title article-title-main", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = []
        section = soup.find(name="div", attrs={"class": "widget-items", "data-widgetname": "ArticleFulltext"})
        if section is not None:
            section = replace_soup_tag(soup=section, new_name="strong", old_name="div", old_attrs={"class": "h7"})
            for sec in split_section(section=section, name="div", class_="h6"):
                if str_strip(sec).lower().startswith("reference"):
                    break
                sections.append(sec)
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        if section.name == "div" and "h6" in section.get_attribute_list("class"):
            return section
        else:
            return None


class LearningMemoryCrawler(GummyAbstJournal):
    """
    URL:
        - https://learnmem.cshlp.org/

    Attributes:
        crawl_type (str) : :meth:`LearningMemoryCrawler's <gummy.journals.LearningMemoryCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name in ["h3", "h4"],
        )

    @staticmethod
    def get_soup_url(url: str) -> str:
        return re.sub(pattern=r"(\.full)?(\.((html)|(pdf)))", repl=".full.html", string=url)

    @staticmethod
    def get_pdf_url(url: str) -> str:
        return re.sub(pattern=r"(\.full)?(\.((html)|(pdf)))", repl=".full.pdf", string=url)

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", attrs={"id": "article-title-1"}, strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = []
        section = soup.find(name="div", class_="article fulltext-view")
        if section is not None:
            for sec in group_soup_with_head(soup=section, name="h2"):
                if find_target_text(soup=sec, name="h2").lower().startswith("reference"):
                    break
                sections.append(sec)
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class ScienceMagCrawler(GummyAbstJournal):
    """
    URL:
        - https://science.sciencemag.org/

    Attributes:
        crawl_type (str) : :meth:`ScienceMagCrawler's <gummy.journals.ScienceMagCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", class_="article__headline", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = []
        abstract = soup.find(name="div", class_="section abstract")
        if abstract is not None:
            sections.append(abstract.__copy__())
        article = soup.find(name="div", class_="article fulltext-view")
        if article is not None:
            if abstract is not None:
                abstract.decompose()
            sections.extend(article.find_all(name=("p", "figure")))
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class PsyChiArtistCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.psychiatrist.com/

    Attributes:
        crawl_type (str) : :meth:`PsyChiArtistCrawler's <gummy.journals.PsyChiArtistCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="p", class_="title-left", strip=True, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = []
        article = soup.find(name="div", attrs={"id": "articlecontent"})
        if article is not None:
            for e in article.find_all(name=("p", "div")):
                if e.get_text().lower().startswith("reference"):
                    break
                sections.append(e)
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        return None


class OncotargetCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.oncotarget.com/

    Attributes:
        crawl_type (str) : :meth:`OncotargetCrawler's <gummy.journals.OncotargetCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h3",
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", attrs={"id": "articleTitle"}, strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = []
        abst_body = soup.find(name="p", class_="BodyText")
        if abst_body is not None:
            abst = BeautifulSoup(markup="", features="lxml").new_tag(name="section")
            abst.append(str2soup("<h2>ABSTRACT</h2>"))
            abst.append(abst_body)
            sections.append(abst)

        section = soup.find(name="div", class_="sns")
        if section is not None:
            article_sections = group_soup_with_head(soup=section, name="h2")
            for sec in article_sections:
                if find_target_text(soup=sec, name="h2", default="head").lower().startswith("reference"):
                    break
                sections.append(sec)
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return None


class ClinicalEndoscopyCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.e-ce.org/

    Attributes:
        crawl_type (str) : :meth:`ClinicalEndoscopyCrawler's <gummy.journals.ClinicalEndoscopyCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h3",  # <h3 class="section-title">
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="h3", class_="PubTitle", strip=True, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = []
        abst = soup.find(name="div", class_="abstract-layer")
        if abst is not None:
            sections.append(abst)
        article = soup.find(name="div", attrs={"id": "article-body"})
        if article is not None:
            sections.extend(article.find_all(name="div", class_="section"))
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h3", class_="main-title")
        return head


class EMBOPressCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.embopress.org

    Attributes:
        crawl_type (str)             : :meth:`EMBOPressCrawler's <gummy.journals.EMBOPressCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", class_="citation__title", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="section", class_="article-section")
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h3", class_="article-section__header")
        return head


class ASPBCrawler(GummyAbstJournal):
    """
    URL:
        - http://www.plantphysiol.org/

    Attributes:
        crawl_type (str)             : :meth:`ASPBCrawlerCrawler's <gummy.journals.ASPBCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "h3",
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", class_="highwire-cite-title", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = []
        article = soup.find(name="div", class_="article fulltext-view")
        if article is not None:
            ref = article.find(name="div", class_="section ref-list")
            if ref is not None:
                ref.decompose()
            sections.extend(group_soup_with_head(article, name="h2"))
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class BiomedGridCrawler(GummyAbstJournal):
    """
    URL:
        - https://biomedgrid.com/

    Attributes:
        crawl_type (str)             : :meth:`BiomedGridCrawler's <gummy.journals.BiomedGridCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", class_="farticle-title citation_title", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = []
        for sec in soup.find_all(name="section", class_="lighten-4"):
            head = self.get_head_from_section(sec)
            if (head is not None) and head.get_text().lower().startswith("reference"):
                break
            sections.append(sec)
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name=("h2", "h4"))
        return head


class NRRCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.nrronline.org/

    Attributes:
        crawl_type (str)             : :meth:`NRRCrawler's <gummy.journals.NRRCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "b",
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="font", class_="sTitle", strip=True, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = []
        start = False
        article = soup.find(name="table", class_="articlepage")
        for sec in group_soup_with_head(article, name="table"):
            if find_target_text(soup=sec, name="table").lower().startswith("abstract"):
                start = True
            if find_target_text(soup=sec, name="table").lower().startswith("reference"):
                break
            if start:
                sections.append(sec)
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="td", class_="pageSub")
        return head


class YMJCrawler(GummyAbstJournal):
    """
    URL:
        - https://eymj.org/

    Attributes:
        crawl_type (str)             : :meth:`YMJCrawler's <gummy.journals.YMJCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "p" and ("tl-lowest-section" in tag.get("class", [])),
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="span", class_="tl-document", strip=True, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = []
        for block in soup.find_all(name="div", attrs={"id": ("article-level-0-front", "article-level-0-body")}):
            sections.extend(group_soup_with_head(soup=block, name="div", class_="tl-main-part"))
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="div", class_="tl-main-part")
        return head


class TheLancetCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.thelancet.com/

    Attributes:
        crawl_type (str) : :meth:`YMJCrawler's <gummy.journals.YMJCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
            isSubheadTags=lambda tag: tag.name == "p" and ("tl-lowest-section" in tag.get("class", [])),
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", class_="article-header__title", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = []
        for sec in soup.find_all(name="section"):
            if find_target_text(soup=sec, name="h2", default="head").lower().startswith("reference"):
                break
            sections.append(sec)
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class FutureScienceCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.future-science.com/

    Attributes:
        crawl_type (str) : :meth:`FutureScienceCrawler's <gummy.journals.FutureScienceCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", class_="citation__title", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = []
        body = soup.find(name="div", class_="article__body")
        if body is not None:
            sections.extend(group_soup_with_head(soup=body, name="h2"))
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class ScitationCrawler(GummyAbstJournal):
    """
    URL:
        - https://aip.scitation.org/
        - https://www.scitation.org/

    Attributes:
        crawl_type (str) : :meth:`ScitationCrawler's <gummy.journals.ScitationCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    @staticmethod
    def get_pdf_url(url: str) -> str:
        return url.replace("/doi/", "/doi/pdf/")

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="h1", strip=True, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", class_="hlFld-Abstract")
        article = soup.find(name="div", class_="hlFld-Fulltext")
        if article is not None:
            for sec in group_soup_with_head(article, name="div", class_="sectionHeading"):
                if find_target_text(soup=sec, name="div", class_="sectionHeading").lower().startswith("reference"):
                    break
                sections.append(sec)
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name=None, class_="sectionHeading")
        return head


class IOPScienceCrawler(GummyAbstJournal):
    """
    URL:
        - https://iopscience.iop.org/

    TODO:
        Deal with **ShieldSquare Captcha**.

    .. image:: _images/ss_captcha.png

    Attributes:
        crawl_type (str) : :meth:`IOPScienceCrawler's <gummy.journals.IOPScienceCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", class_="wd-jnl-art-title", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", class_="article-content")
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class AACRPublicationsCrawler(GummyAbstJournal):
    """
    URL:
        - https://aacrjournals.org/
        - https://bloodcancerdiscov.aacrjournals.org/
        - https://cancerdiscovery.aacrjournals.org
        - https://cebp.aacrjournals.org
        - https://cancerimmunolres.aacrjournals.org/
        - https://cancerpreventionresearch.aacrjournals.org/
        - https://cancerres.aacrjournals.org/
        - https://clincancerres.aacrjournals.org/
        - https://mcr.aacrjournals.org/
        - https://mct.aacrjournals.org/

    Attributes:
        crawl_type (str) : :meth:`AACRPublicationsCrawler's <gummy.journals.AACRPublicationsCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup, name="h1", class_="highwire-cite-title", strip=True, default=self.default_title
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = []
        for sec in soup.find_all(name="div", class_=("section", "boxed-text")):
            head = self.get_head_from_section(sec)
            if (head is not None) and head.get_text().lower().startswith("reference"):
                break
            sections.append(sec)
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name=("h2", "h3"))
        return head


class PsycNetCrawler(GummyAbstJournal):
    """
    URL:
        - https://psycnet.apa.org/

    Attributes:
        crawl_type (str) : :meth:`PsycNetCrawler's <gummy.journals.PsycNetCrawlerCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    def make_elements_visible(self, driver):
        wait_until_all_elements(driver=driver, timeout=5, verbose=self.verbose)

    @staticmethod
    def is_request_successful(soup):
        """Check whether request is successful or not.

        Args:
            soup (BeautifulSoup) : A data structure representing a parsed HTML or XML document.
        """
        if soup.get_text().startswith("Request unsuccessful"):
            raise RequestException(
                toRED("[403 Forbidden]\n") + soup.get_text() + toGREEN("\nPlease run Chrome with GUI browser.")
            )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        self.is_request_successful(soup)
        title = self.default_title
        article_title = soup.find(name="div", class_="articleTitleGroup")
        if article_title is not None:
            title = find_target_text(soup=article_title, name="h1", strip=True, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = []
        abst = soup.find(name="div", class_="abstractsContainer")
        if abst is not None:
            abst.append("<h3>Abstract</h3>")
        body = soup.find(name="div", class_="articleBody")
        if body is not None:
            sections.extend(body.find_all(name="div", class_="section ftJumpToAnchor"))
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h3")
        return head


class MinervaMedicaCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.minervamedica.it/

    Attributes:
        crawl_type (str) : :meth:`MinervaMedicaCrawler's <gummy.journals.MinervaMedicaCrawlerCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    @staticmethod
    def get_soup_url(url: str) -> str:
        return f"https://www.minervamedica.it/en/journals/minerva-anestesiologica/article.php?cod={list(urllib.parse.parse_qs(url).values())[0][0]}"

    def make_elements_visible(self, driver):
        try_find_element_click(driver=driver, by="xpath", identifier='//*[@id="pluto"]/div/p/a[1]')
        wait_until_all_elements(driver=driver, timeout=self.sleep_for_loading, verbose=self.verbose)

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="title", strip=True, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = []
        siteloader = soup.find(name="div", attrs={"id": "siteloader"})
        if siteloader is not None:
            sections.extend(
                siteloader.find_all(
                    name=None,
                    class_=("Abstract-Head", "Abstract", "Head1", "Paragraph-Post-Head", "Paragraph", "BOX-IMMAGINE"),
                )
            )
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="p", class_=("Head1", "Abstract-Head"))
        return head


class JNeurosciCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.jneurosci.org/

    Attributes:
        crawl_type (str) : :meth:`JNeurosciCrawler's <gummy.journals.JNeurosciCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    @staticmethod
    def get_soup_url(url: str) -> str:
        for t in [".full", ".abstract", ".full.pdf"]:
            url = url.rstrip(t)
        return url.replace("/content/jneuro/", "/content/")

    @staticmethod
    def get_pdf_url(url: str) -> str:
        return JNeurosciCrawler.get_soup_url(url).replace("/content/", "/content/jneuro/") + ".full.pdf"

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(
            soup=soup,
            name="h1",
            class_="highwire-cite-title",
            attrs={"id": "page-title"},
            strip=True,
            default=self.default_title,
        )
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = soup.find_all(name="div", class_="section")
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class HindawiCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.hindawi.com/

    Attributes:
        crawl_type (str) : :meth:`HindawiCrawler's <gummy.journals.HindawiCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="h1", class_="article_title", strip=True, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        """

        .. code-block:: html

            <article>
                <div class="xml-content"> paper content </div>
                <div class="xml-content"> References </div>
                <div class="xml-content"> Copyright </div>
            </article>
        """
        sections = []
        article = soup.find(name="article", class_="article_body")
        if article is not None:
            xml_content = article.find(name="div", class_="xml-content")
            if xml_content is not None:
                sections.extend(group_soup_with_head(soup=xml_content, name="h4"))
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h4")
        return head


class ChemRxivCrawler(GummyAbstJournal):
    """
    URL:
        - https://chemrxiv.org/

    Attributes:
        crawl_type (str) : :meth:`ChemRxivCrawler's <gummy.journals.ChemRxivCrawler>` default ``crawl_type`` is ``"pdf"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="pdf",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    @staticmethod
    def get_pdf_url(url: str) -> str:
        soup = BeautifulSoup(markup=requests.get(ChemRxivCrawler.get_soup_url(url)).content, features="html.parser")
        if soup is not None:
            div = soup.find(name="div", class_="_2FHUU")
            if div is not None:
                a = div.find(name="a", class_=("_2PSMA", "_1jrLT", "_3kcSK", "_27tHP", "_2BFqb"))
                if a is not None:
                    url = a.get("href")
        return url

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="h1", strip=True, default=self.default_title)  # class_="_3lGK4"
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections = []
        div = soup.find(name="div", class_="VCg-j")
        if div is not None:
            sections.extend(div.find_all(name="div", class_="_3nx2Q"))
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


class ScienceDailyCrawler(GummyAbstJournal):
    """
    URL:
        - https://www.sciencedaily.comy

    Attributes:
        crawl_type (str) : :meth:`ScienceDailyCrawler's <gummy.journals.ScienceDailyCrawler>` default ``crawl_type`` is ``"soup"``.
    """

    def __init__(
        self,
        gateway: Union[str, gateways.GummyAbstGateWay] = "useless",
        sleep_for_loading: int = 3,
        verbose: bool = True,
        **kwargs,
    ):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            verbose=verbose,
        )

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = find_target_text(soup=soup, name="h1", attrs={"id": "headline"}, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections: List[BeautifulSoup] = []
        article: BeautifulSoup = soup.find(name="div", attrs={"id": "story_text"})
        if article is not None:
            sections.extend(
                group_soup_with_head(soup=article, name="div", class_="mobile-top-rectangle hidden-md hidden-lg")
            )
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="p", class_="lead")
        return head


class AnnualReviewsCrawler(GummyAbstJournal):
    """
    URL:
        - https://www-annualreviews-org/

    Attributes:
        crawl_type (str) : :meth:`AnnualReviewsCrawler's <gummy.journals.AnnualReviewsCrawler>` default ``crawl_type`` is ``"pdf"``.
    """

    def __init__(self, gateway: str = "useless", sleep_for_loading: int = 3, verbose: bool = True, **kwargs):
        super().__init__(
            crawl_type="soup",
            gateway=gateway,
            sleep_for_loading=sleep_for_loading,
            isSubheadTags=lambda tag: tag.name in ["h3", "h4"],
            verbose=verbose,
        )
        self.register_decompose_soup_tags(name="div", class_="lit-cited")
        self.register_decompose_soup_tags(name="a", class_="scrollRef")

    def get_title_from_soup(self, soup: BeautifulSoup) -> str:
        title = ""
        section = soup.find(name="section", class_="ar-content-left-col")
        if section is not None:
            title = find_target_text(soup=section, name="h1", strip=True, default=self.default_title)
        return title

    def get_sections_from_soup(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        sections: List[BeautifulSoup] = []

        article_abstract: BeautifulSoup = soup.find(name="div", class_="hlFld-Abstract")
        if article_abstract is not None:
            sections.extend(group_soup_with_head(soup=article_abstract, name="h2"))

        article_full_text: BeautifulSoup = soup.find(name="div", class_="hlFld-Fulltext")
        if article_full_text is not None:
            sections.extend(group_soup_with_head(soup=article_full_text, name="h2"))
        return sections

    def get_head_from_section(self, section: BeautifulSoup) -> BeautifulSoup:
        head = section.find(name="h2")
        return head


all = TranslationGummyJournalCrawlers = {
    "pdf": PDFCrawler,
    "arxiv": arXivCrawler,
    "nature": NatureCrawler,
    "ncbi": NCBICrawler,
    "pubmed": PubMedCrawler,
    "oxfordacademic": OxfordAcademicCrawler,
    "sciencedirect": ScienceDirectCrawler,
    "springer": SpringerCrawler,
    "mdpi": MDPICrawler,
    "unioklahoma": UniOKLAHOMACrawler,
    "lungcancer": LungCancerCrawler,
    "cellpress": CellPressCrawler,
    "wileyonlinelibrary": WileyOnlineLibraryCrawler,
    "jbc": JBCCrawler,
    "biologists": BiologistsCrawler,
    "biomedcentral": BioMedCentralCrawler,
    "ieeexplore": IEEEXploreCrawler,
    "jstage": JSTAGECrawler,
    "acspublications": ACSPublicationsCrawler,
    "unikeio": UniKeioCrawler,
    "plosone": PLOSONECrawler,
    "frontiers": frontiersCrawler,
    "rnajournal": RNAjournalCrawler,
    "intechopen": IntechOpenCrawler,
    "nrcresearchpress": NRCResearchPressCrawler,
    "spandidos": SpandidosCrawler,
    "taylorandfrancisonline": TaylorandFrancisOnlineCrawler,
    "biorxiv": bioRxivCrawler,
    "rscpublishing": RSCPublishingCrawler,
    "jsse": JSSECrawler,
    "science": ScienceCrawler,
    "medrxiv": medRxivCrawler,
    "aclanthology": ACLAnthologyCrawler,
    "pnas": PNASCrawler,
    "ams": AMSCrawler,
    "acm": ACMCrawler,
    "aps": APSCrawler,
    "asip": ASIPCrawler,
    "renalphysiology": RenalPhysiologyCrawler,
    "genetics": GeneticsCrawler,
    "genedev": GeneDevCrawler,
    "jamanetwork": JAMANetworkCrawler,
    "sagejournals": SAGEjournalsCrawler,
    "molcellbio": MolCellBioCrawler,
    "jkms": JKMSCrawler,
    "jkns": JKNSCrawler,
    "bioscience": BioscienceCrawler,
    "radiographics": RadioGraphicsCrawler,
    "pediatricsurgery": PediatricSurgeryCrawler,
    "nejm": NEJMCrawler,
    "lwwjournals": LWWJournalsCrawler,
    "arvojournals": ARVOJournalsCrawler,
    "learningmemory": LearningMemoryCrawler,
    "psychiartist": PsyChiArtistCrawler,
    "oncotarget": OncotargetCrawler,
    "clinicalendoscopy": ClinicalEndoscopyCrawler,
    "embopress": EMBOPressCrawler,
    "aspb": ASPBCrawler,
    "biomedgrid": BiomedGridCrawler,
    "nrr": NRRCrawler,
    "ymj": YMJCrawler,
    "thelancet": TheLancetCrawler,
    "futurescience": FutureScienceCrawler,
    "scitation": ScitationCrawler,
    "iopscience": IOPScienceCrawler,
    "aacrpublications": AACRPublicationsCrawler,
    "psycnet": PsycNetCrawler,
    "minervamedica": MinervaMedicaCrawler,
    "jneurosci": JNeurosciCrawler,
    "hindawi": HindawiCrawler,
    "chemrxiv": ChemRxivCrawler,
    "sciencedaily": ScienceDailyCrawler,
    "annualreviews": AnnualReviewsCrawler,
}

get = mk_class_get(all_classes=TranslationGummyJournalCrawlers, gummy_abst_class=[GummyAbstJournal], genre="journals")
