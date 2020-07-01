# coding: utf-8

from .journal import get_contents
from .render import make_content, render_paper
from . import translators
from .utils import get_driver

def make_html(url, path=None, translator="deepl", journal_type=None):
    with get_driver() as driver:
        title, texts = get_contents(url=url, driver=driver, journal_type=journal_type)
        translator = translators.get(identifier=translator, driver=driver, trials=20, verbose=False)

        contents = []
        for (headline, text) in texts:
            ja = translator.en2ja(query=text)
            content = make_content(headline=headline, en=text, ja=ja)
            contents.append(content)
        contents = "\n".join(contents)

        if path is None:
            path = title + ".html"
        render_paper(path=path, title=title, contents=contents)