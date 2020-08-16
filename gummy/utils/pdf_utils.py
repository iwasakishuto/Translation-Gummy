# coding: utf-8
import io
import os
import base64
import urllib
import werkzeug
import contextlib
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTContainer, LTTextBox, LTImage, LTTextLine, LTFigure
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage

from ._path import GUMMY_DIR
from .coloring_utils import toRED, toBLUE
from .download_utils import download_file

@contextlib.contextmanager
def handlePDF(file, dirname=GUMMY_DIR):
    if isinstance(file, werkzeug.datastructures.FileStorage) or isinstance(file, io.TextIOWrapper):
        yield PDFPage.get_pages(fp=file)
        # return pages
    else:
        print(file)
        if isinstance(file, str) and (not os.path.exists(file)):
            path = download_file(url=file, dirname=dirname)
            if path is None:
                print(toRED(f"Failed to download PDF from {toBLUE(file)}"))
        else:
            path = file
        with open(path, mode="rb") as f_pdf:
            yield PDFPage.get_pages(fp=f_pdf)

def parser_pdf_pages(layout_objs):
    texts = []
    for lt_obj in layout_objs:
        if isinstance(lt_obj, LTTextBox) or isinstance(lt_obj, LTTextLine):
            texts.append(lt_obj.get_text())
        elif isinstance(lt_obj, LTImage):
            rawdata = lt_obj.stream.get_rawdata()
            bs64data = base64.b64encode(rawdata).decode("utf-8")
            texts.append(f'<img src="data:image/jpeg;base64,{bs64data}" />')
        elif isinstance(lt_obj, LTFigure):
            texts.extend(parser_pdf_pages(lt_obj._objs))
    return texts

def getPDFPages(file):
    # Settings.
    rsrcmgr     = PDFResourceManager()
    laparams    = LAParams(detect_vertical=True)
    device      = PDFPageAggregator(rsrcmgr=rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr=rsrcmgr, device=device)
    #  parse PDF pages
    pdf_pages = []
    with handlePDF(file=file) as pages:
        for page in pages:
            interpreter.process_page(page)
            layout = device.get_result()
            pdf_pages.append(parser_pdf_pages(layout_objs=layout._objs))
    return pdf_pages
