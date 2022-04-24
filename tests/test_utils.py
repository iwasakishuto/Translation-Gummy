# coding: utf-8
from typing import List

import pytest
from gummy import journals
from gummy.utils import get_driver, whichJournal

from data import JournalData


@pytest.mark.parametrize("journal_type", list(JournalData.keys()))
def test_whichJournal(db, journal_type: str):
    urls: List[str] = db.journals.get(journal_type)
    with get_driver() as driver:
        for url in urls:
            assert whichJournal(url=url, driver=None) == journal_type
            assert whichJournal(url=url, driver=driver) == journal_type
            crawler = journals.get(journal_type)
            assert crawler.journal_type == journal_type
