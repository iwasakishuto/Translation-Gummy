# coding: utf-8
from gummy.utils import get_driver
from gummy import translators

def _test_translators(db, identifier, **kwargs):
    with get_driver() as driver:
        translator = translators.get(identifier, driver=driver, maxsize=1000)
        ja_simple_sentence    = translator.en2ja(query=db.sentences.get("simple_sentence"))
        ja_multiple_sentences = translator.en2ja(query=db.sentences.get("multiple_sentences"))
        ja_SteveJobsSpeech    = translator.en2ja(query=db.sentences.get("SteveJobsSpeech"))

    assert len(ja_simple_sentence) > 0
    assert len(ja_multiple_sentences) > 0
    assert len(ja_SteveJobsSpeech) > 0

def test_google_translators(db):
    _test_translators(db=db, identifier="google")

def test_deepl_translators(db):
    _test_translators(db=db, identifier="deepl")