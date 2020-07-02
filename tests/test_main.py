# coding: utf-8
import os
from gummy.main import make_html, make_pdf

def test_journal2html():
    htmlpath = make_html(url="https://arxiv.org/abs/2003.03253")
    os.remove(htmlpath)

def test_journal2pdf():
    pdfpath = make_pdf(url="https://arxiv.org/abs/2003.03253")
    os.remove(pdfpath)