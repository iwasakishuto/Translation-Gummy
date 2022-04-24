# coding: utf-8
from typing import List

import pytest
from gummy import journals
from gummy.utils import get_driver

from data import JournalData


@pytest.mark.parametrize("journal_type", list(JournalData.keys()))
def test_journals(db, journal_type: str, gateway: str = "useless", **kwargs):
    urls: List[str] = db.journals.get(journal_type)
    for url in urls:
        crawler: journals.GummyAbstJournal = journals.get(identifier=journal_type, gateway=gateway)
        with get_driver() as driver:
            title, texts = crawler.get_contents(url=url, driver=driver)

        assert len(title) > 0
        assert len(texts) > 0
