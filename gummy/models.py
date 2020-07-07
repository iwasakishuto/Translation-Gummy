# coding: utf-8
import os
from . import translators
from .journal import get_contents
from .utils import tohtml, html2pdf
from .utils import get_driver
from .utils import GUMMY_DIR, TEMPLATES_DIR

def make_html(url, path=None, translator="deepl", journal_type=None, 
              searchpath=TEMPLATES_DIR, template="paper.tpl"):
    with get_driver() as driver:
        title, texts = get_contents(url=url, driver=driver, journal_type=journal_type)
        translator = translators.get(identifier=translator, driver=driver, trials=20, verbose=False)

        contents = []
        for (headline, text) in texts:
            ja = translator.en2ja(query=text)
            content = dict(headline=headline, en=text, ja=ja)
            contents.append(content)

        if path is None:
            path = os.path.join(GUMMY_DIR, title + ".html")
        htmlpath = tohtml(path=path, title=title, contents=contents, searchpath=searchpath, template=template)

    return htmlpath

def make_pdf(url, path=None, translator="deepl", journal_type=None, 
             searchpath=TEMPLATES_DIR, template="paper.tpl",
             delete_html=True, options=None):
    htmlpath = make_html(
        url=url, path=path, translator=translator, journal_type=journal_type,
        searchpath=searchpath, template=template,
    )
    pdfpath = html2pdf(path=htmlpath, delete_html=delete_html, options=options)
    return pdfpath