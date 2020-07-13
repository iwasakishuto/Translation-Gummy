# coding: utf-8
import pytest
from gummy.utils import whichJournal
from data import JournalData

@pytest.mark.parametrize("journal_type", list(JournalData.keys()))
def test_whichJournal(db, journal_type):
    url = db.journals.get(journal_type)
    assert whichJournal(url=url) == journal_type
