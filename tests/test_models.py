# coding: utf-8
import os
from gummy.models import TranslationGummy

def _test_models(db, url, gateway="utokyo", translator="deepl"):
    gummy = TranslationGummy(gateway=gateway, translator=translator)

    # # Simple translation
    # ja_simple_sentence    = gummy.en2ja(query=db.simple_sentence)
    # ja_multiple_sentences = gummy.en2ja(query=db.multiple_sentences)
    # ja_SteveJobsSpeech    = gummy.en2ja(query=db.SteveJobsSpeech)
    # assert len(ja_simple_sentence) > 0
    # assert len(ja_multiple_sentences) > 0
    # assert len(ja_SteveJobsSpeech) > 0

    # Make HTML & PDF.
    htmlpath = gummy.toHTML(url=url)
    os.remove(htmlpath)
    pdfpath  = gummy.toPDF(url=url, delete_html=True)
    os.remove(pdfpath)

def test_model_all(db):
    for url in ["https://arxiv.org/abs/2003.03253", "https://doi.org/10.1038/171737a0"]:
        for gateway in ["utokyo"]:
            for translator in ["deepl", "google"]:
                _test_models(db=db, url=url, gateway=gateway, translator=translator)