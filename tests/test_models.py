# coding: utf-8
import os
import pytest
from gummy.models import TranslationGummy
from gummy import gateways
from gummy import translators
from gummy.utils import get_driver

from data import JournalData

@pytest.mark.parametrize("url", list(JournalData.values()))
@pytest.mark.parametrize("gateway", list(gateways.all.keys()))
@pytest.mark.parametrize("translator", list(translators.all.keys()))
def test_models(db, url, gateway, translator):
    with get_driver() as driver:
        gummy = TranslationGummy(driver=driver, gateway=gateway, translator=translator)    
        # Make HTML & PDF.
        pdfpath  = gummy.toPDF(url=url, delete_html=True)
        os.remove(pdfpath)
