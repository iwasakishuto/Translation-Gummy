# coding: utf-8
import os
from kerasy.utils import toACCENT

from . import gateways
from . import journals
from . import translators
from .utils.journal_utils import whichJournal
from .utils.outfmt_utils import tohtml, html2pdf
from .utils.driver_utils import get_driver
from .utils._path import GUMMY_DIR, TEMPLATES_DIR

class TranslationGummy():
    def __init__(self, chrome_options=None, gateway="useless", translator="deepl"):
        self.driver = get_driver(chrome_options=chrome_options)
        self.gateway = gateway
        self.translator = translators.get(translator)

    def en2ja(self, query):
        return self.translator.en2ja(query=query, driver=self.driver)

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
        for content in contents:
            log = f"[{toACCENT(content.get('headline'))}] " if "headline" in content else "\t"
            if "en" in content:
                en = content.get("en", "")
                # ===== TRANSLATION ======
                ja = self.en2ja(query=en)
                content["ja"] = ja
                # ========================
                log += f"{' '.join(en.split(' ')[:3])}... -> {ja[:6]}..."
            elif "img" in content: 
                log += "<img>"
            print(log)
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
        pdfpath = html2pdf(path=htmlpath, delete_html=delete_html, options=options)
        return pdfpath