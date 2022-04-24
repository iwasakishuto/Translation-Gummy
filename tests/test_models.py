# coding: utf-8
import os

import pytest
from gummy import gateways, translators
from gummy.models import TranslationGummy
from gummy.utils import get_driver

from data import JournalData


@pytest.mark.parametrize("gateway", list(gateways.all.keys()))
@pytest.mark.parametrize("translator", list(translators.all.keys()))
def test_models(db, gateway: str, translator: str, journal_type: str = "nature"):
    url: str = db.journals.get(journal_type)[0]
    with get_driver() as driver:
        gummy = TranslationGummy(driver=driver, gateway=gateway, translator=translator)
        # Make HTML & PDF.
        pdfpath: str = gummy.toPDF(url=url, delete_html=True)
        os.remove(pdfpath)
