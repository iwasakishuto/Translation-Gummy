# coding: utf-8
import os
from kerasy.utils import toACCENT, toBLUE, toGREEN

from . import gateways
from . import journals
from . import translators

from .utils._path import GUMMY_DIR, TEMPLATES_DIR
from .utils.driver_utils import get_driver
from .utils.journal_utils import whichJournal
from .utils.outfmt_utils import tohtml, html2pdf
from .utils.driver_utils import get_driver

class TranslationGummy():
    def __init__(self, chrome_options=None, browser=False, driver=None, 
                 gateway="useless", translator="deepl"):
        if driver is None:
            driver = get_driver(chrome_options=chrome_options, browser=browser)
        self.driver = driver
        self.gateway = gateway
        self.translator = translators.get(translator)

    def en2ja(self, query, barname=None):
        return self.translator.en2ja(query=query, driver=self.driver, barname=barname)

    def get_contents(self, url, journal_type=None, gateway=None, **gatewaykwargs):
        if journal_type is None:
            journal_type = whichJournal(url)
        gateway = gateway or self.gateway
        crawler = journals.get(journal_type, gateway=gateway, sleep_for_loading=3)
        title, texts = crawler.get_contents(url=url, driver=self.driver)
        return title, texts

    def toHTML(self, url, path=None, journal_type=None, gateway=None, 
               searchpath=TEMPLATES_DIR, template="paper.tpl", 
               **gatewaykwargs):
        title, contents = self.get_contents(url=url, journal_type=journal_type, gateway=gateway, **gatewaykwargs)

        print(f"\nTranslation: {self.translator.name}")
        print("="*30)
        len_contents = len(contents)
        for i,content in enumerate(contents):
            barname = f"[{i+1:>0{len(str(len_contents))}}/{len_contents}] " + toACCENT(content.get("headline","\t"))            
            if "en" in content:
                en = content.get("en", "")
                # ===== TRANSLATION ======
                ja = self.en2ja(query=en, barname=barname)
                content["ja"] = ja
                # ========================
            elif "img" in content:
                print(barname + "<img>")
        if path is None:
            path = os.path.join(GUMMY_DIR, title + ".html")
        htmlpath = tohtml(path=path, title=title, contents=contents, searchpath=searchpath, template=template)
        return htmlpath

    def toPDF(self, url, path=None, journal_type=None, gateway=None, 
              searchpath=TEMPLATES_DIR, template="paper.tpl",
              delete_html=True, options=None, 
              **gatewaykwargs):
        htmlpath = self.toHTML(
            url=url, path=path, journal_type=journal_type, gateway=gateway, 
            searchpath=searchpath, template=template,
            **gatewaykwargs
        )
        print("Convert from HTML to PDF")
        print("="*30)
        pdfpath = html2pdf(path=htmlpath, delete_html=delete_html, options=options)
        return pdfpath