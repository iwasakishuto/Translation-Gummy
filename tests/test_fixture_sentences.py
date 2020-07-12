#coding: utf-8

def test_sentences(db):
    simple_sentence    = db.sentences.get("simple_sentence")
    multiple_sentences = db.sentences.get("multiple_sentences")
    SteveJobsSpeech    = db.sentences.get("SteveJobsSpeech")

    assert simple_sentence    is not None
    assert multiple_sentences is not None
    assert SteveJobsSpeech    is not None

    assert len(simple_sentence)    < len(multiple_sentences)
    assert len(multiple_sentences) < len(SteveJobsSpeech)