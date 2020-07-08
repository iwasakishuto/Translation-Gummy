# coding: utf-8
import os
from gummy.models import TranslationGummy
from gummy import gateways
from gummy import translators

def _test_models(db, url, gateway="utokyo", translator="deepl"):
    gummy = TranslationGummy(gateway=gateway, translator=translator)
    
    # Make HTML & PDF.
    htmlpath = gummy.toHTML(url=url)
    os.remove(htmlpath)
    pdfpath  = gummy.toPDF(url=url, delete_html=True)
    os.remove(pdfpath)

def test_model_all(db):
    for url in ["https://arxiv.org/abs/2003.03253", "https://doi.org/10.1038/171737a0"]:
        for gateway in gateways.all.keys():
            for translator in translators.all.keys():
                _test_models(db=db, url=url, gateway=gateway, translator=translator)