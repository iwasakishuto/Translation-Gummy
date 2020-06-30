# coding: utf-8

from .journal import get_contents
from .render import make_content, render_paper
from .translation import deepl_en2ja
from .utils import get_driver

def make_html(url, path=None, journal_type=None):
    with get_driver() as driver:
        title, texts = get_contents(url=url, driver=driver, journal_type=journal_type)

        contents = []
        for (headline, text) in texts:
            ja = deepl_en2ja(driver=driver, query=text, timeout=1, trials=20, verbose=0)
            content = make_content(headline=headline, en=text, ja=ja)
            contents.append(content)
        contents = "\n".join(contents)

        if path is None:
            path = title + ".html"
        render_paper(path=path, title=title, contents=contents)