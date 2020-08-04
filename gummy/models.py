# coding: utf-8
import os
import time

from . import gateways
from . import journals
from . import translators

from .utils._path import GUMMY_DIR, TEMPLATES_DIR
from .utils.coloring_utils import toACCENT, toBLUE, toGREEN
from .utils.driver_utils import get_driver
from .utils.journal_utils import whichJournal
from .utils.outfmt_utils import sanitize_filename, tohtml, html2pdf
from .utils.driver_utils import get_driver

class TranslationGummy():
    def __init__(self, chrome_options=None, browser=False, driver=None, 
                 gateway="useless", translator="deepl", verbose=True,
                 translator_verbose=False):
        if driver is None:
            driver = get_driver(chrome_options=chrome_options, browser=browser)
        self.driver = driver
        self.gateway = gateway
        self.translator = translators.get(translator, verbose=translator_verbose)
        self.verbose=verbose

    def en2ja(self, query, barname=None):
        return self.translator.en2ja(query=query, driver=self.driver, barname=barname)

    def get_contents(self, url, journal_type=None, crawl_type=None, gateway=None, **gatewaykwargs):
        if os.path.exists(url):
            journal_type = "pdf"
        elif journal_type is None:
            journal_type = whichJournal(url, driver=self.driver, verbose=self.verbose)
        gateway = gateway or self.gateway
        crawler = journals.get(
            journal_type, 
            gateway=gateway, sleep_for_loading=3, verbose=self.verbose, maxsize=self.translator.maxsize
        )
        title, texts = crawler.get_contents(url=url, driver=self.driver, crawl_type=crawl_type)
        return title, texts

    def toHTML(self, url, path=None, out_dir=GUMMY_DIR,
               journal_type=None, crawl_type=None, gateway=None,
               searchpath=TEMPLATES_DIR, template="paper.tpl", 
               **gatewaykwargs):
        """ URL to HTML.
        @params url                 : URL of a page you want to create a pdf
        @params path/out_dir        : Where you save a created HTML. If path is None, save at <out_dir>/<title>.html
        @params journal_type        : If you specify, use <journal_type> journal crawler.
        @params crawl-type          : Crawling type, if you not specify, use recommended crawling type.
        @params gateway             : Gateway identifier, string name of a gateway.
        @params searchpath/template : Use a <searchpath>/<template> tpl for creating HTML.
        """
        title, contents = self.get_contents(
            url=url, journal_type=journal_type, crawl_type=crawl_type, 
            gateway=gateway, **gatewaykwargs
        )
        print(f"\nTranslation: {toACCENT(self.translator.name)}\n{'='*30}")
        len_contents = len(contents)
        for i,content in enumerate(contents):
            barname = f"[{i+1:>0{len(str(len_contents))}}/{len_contents}] " + toACCENT(content.get("headline","\t"))            
            if "en" in content:
                # ===== TRANSLATION ======
                ja = self.en2ja(query=content["en"], barname=barname)
                content["ja"] = ja
                # ========================
            elif "img" in content and self.verbose:
                print(barname + "<img>")
        if path is None:
            path = os.path.join(out_dir, sanitize_filename(fn=title, ext=".html"))
        htmlpath = tohtml(
            path=path, title=title, contents=contents, 
            searchpath=searchpath, template=template, verbose=self.verbose
        )
        return htmlpath

    def toPDF(self, url, path=None, out_dir=GUMMY_DIR,
              journal_type=None, crawl_type=None, gateway=None, 
              searchpath=TEMPLATES_DIR, template="paper.tpl",
              delete_html=True, options={}, 
              **gatewaykwargs):
        htmlpath = self.toHTML(
            url=url, path=path, out_dir=out_dir,
            journal_type=journal_type, crawl_type=crawl_type, gateway=gateway, 
            searchpath=searchpath, template=template,
            **gatewaykwargs
        )
        if self.verbose: print(f"Convert from HTML to PDF\n{'='*30}")
        pdfpath = html2pdf(path=htmlpath, delete_html=delete_html, verbose=self.verbose, options=options)
        return pdfpath