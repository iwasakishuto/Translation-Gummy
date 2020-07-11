# coding: utf-8
from gummy.utils import get_driver
from gummy import journals

def _test_journals(identifier, url, gateway="useless", **kwargs):
    crawler = journals.get(identifier, gateway=gateway)
    with get_driver() as driver:
        title, texts = crawler.get_contents(url=url, driver=driver)
        
    assert len(title) > 0
    assert len(texts) > 0

def test_arXiv():
    _test_journals(identifier="arXiv", url="https://arxiv.org/abs/2003.03253")

def test_Nature():
    _test_journals(identifier="Nature", url="https://doi.org/10.1038/171737a0")

def test_PubMed():
    _test_journals(identifier="PubMed", url="https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5325678/")
