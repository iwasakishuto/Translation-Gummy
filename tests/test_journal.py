# coding: utf-8
from gummy.utils import get_driver
from gummy import journal

def _test_journal(identifier, url, **kwargs):
    get_contents = journal.get(identifier)
    with get_driver() as driver:
        title, texts = get_contents(url, driver=driver, need_gateway=False, **kwargs)

    assert len(title) > 0
    assert len(texts) > 0

def test_arXiv():
    _test_journal(identifier="arXiv", url="https://arxiv.org/abs/2003.03253")

def test_Nature():
    _test_journal(identifier="Nature", url="https://doi.org/10.1038/171737a0")
