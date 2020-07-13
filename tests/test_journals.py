# coding: utf-8
import pytest
from gummy.utils import get_driver
from gummy import journals
from data import JournalData

@pytest.mark.parametrize("journal_type", list(JournalData.keys()))
def test_journals(db, journal_type, gateway="useless", **kwargs):
    url = db.journals.get(journal_type)
    crawler = journals.get(identifier=journal_type, gateway=gateway)
    with get_driver() as driver:
        title, texts = crawler.get_contents(url=url, driver=driver)
        
    assert len(title) > 0
    assert len(texts) > 0