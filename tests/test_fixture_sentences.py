#coding: utf-8

def test_sentences(db):
    simple_sentence    = db.__dict__.get("simple_sentence")
    multiple_sentences = db.__dict__.get("multiple_sentences")
    SteveJobsSpeech    = db.__dict__.get("SteveJobsSpeech")

    assert simple_sentence    is not None
    assert multiple_sentences is not None
    assert SteveJobsSpeech    is not None

    assert len(simple_sentence)    < len(multiple_sentences)
    assert len(multiple_sentences) < len(SteveJobsSpeech)