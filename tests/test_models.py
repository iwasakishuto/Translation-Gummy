# coding: utf-8
import os
import pytest
from gummy.models import TranslationGummy
from gummy import gateways
from gummy import translators

@pytest.mark.parametrize("url", ["https://arxiv.org/abs/2003.03253", "https://doi.org/10.1038/171737a0"])
@pytest.mark.parametrize("gateway", list(gateways.all.keys()))
@pytest.mark.parametrize("translator", list(translators.all.keys()))
def test_models(db, url, gateway, translator):
    gummy = TranslationGummy(gateway=gateway, translator=translator)
    
    # Make HTML & PDF.
    htmlpath = gummy.toHTML(url=url)
    os.remove(htmlpath)
    pdfpath  = gummy.toPDF(url=url, delete_html=True)
    os.remove(pdfpath)
