# coding: utf-8
import os
import pytest
from gummy.models import TranslationGummy
from gummy import gateways
from gummy import translators

from data import JournalData

@pytest.mark.parametrize("url", list(JournalData.values()))
@pytest.mark.parametrize("gateway", list(gateways.all.keys()))
@pytest.mark.parametrize("translator", list(translators.all.keys()))
def test_models(db, url, gateway, translator):
    gummy = TranslationGummy(gateway=gateway, translator=translator)
    
    # Make HTML & PDF.
    htmlpath = gummy.toHTML(url=url)
    os.remove(htmlpath)
    pdfpath  = gummy.toPDF(url=url, delete_html=True)
    os.remove(pdfpath)
