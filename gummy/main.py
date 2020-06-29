# coding: utf-8

from .journal import get_from_nature
from .render import make_content, render_paper
from .deepl import en2ja
from .utils import get_driver

def make_html(url, path=None):
    with get_driver() as driver:
        title, texts = get_from_nature(url=url, driver=driver)

        contents = []
        for (headline, text) in texts:
            ja = en2ja(driver=driver, query=text, timeout=1, trials=20, verbose=0)
            content = make_content(headline=headline, en=text, ja=ja)
            contents.append(content)
        contents = "\n".join(contents)

        if path is None:
            path = title + ".html"
        render_paper(path=path, title=title, contents=contents)