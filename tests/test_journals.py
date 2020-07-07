# coding: utf-8
from gummy.utils import get_driver
from gummy import journals

def _test_journals(identifier, url, **kwargs):
    crawler = journals.get(identifier)
    with get_driver() as driver:
        title, texts = crawler.get_contents(url=url, driver=driver)
        
    assert len(title) > 0
    assert len(texts) > 0

def test_arXiv():
    _test_journals(identifier="arXiv", url="https://arxiv.org/abs/2003.03253")

def test_Nature():
    _test_journals(identifier="Nature", url="https://doi.org/10.1038/171737a0")
