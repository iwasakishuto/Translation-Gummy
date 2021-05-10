# coding: utf-8
"""Utility programs for handling and analyzing PDF file."""
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
from .compress_utils import extract_from_compressed, is_compressed
from .download_utils import download_file, match2path

@contextlib.contextmanager
def get_pdf_pages(file, dirname=GUMMY_DIR):
    """Get PDF pages.

    Args:
        file (data, str) : url or path or data of PDF.
        dirname (str)    : if ``file`` is url, download and save it to ``dirname``. (defalt= ``GUMMY_DIR``)
    """
    if isinstance(file, werkzeug.datastructures.FileStorage) or isinstance(file, io.TextIOWrapper):
        yield PDFPage.get_pages(fp=file)
    else:
        path = match2path(file, dirname=dirname)
        with open(path, mode="rb") as f_pdf:
            yield PDFPage.get_pages(fp=f_pdf)

def parser_pdf_pages(layout_objs):
    """Parse PDF pages and get contents in order.

    Args:
        layout_objs (list) : Each element is pdfminer.layout object.

    Returns:
        list : Each element is a list which contains [text, bbox(x0,y0,x1,y1)]
    """
    objects = []
    for lt_obj in layout_objs:
        if isinstance(lt_obj, LTTextBox) or isinstance(lt_obj, LTTextLine):
            objects.append([lt_obj.get_text(), lt_obj.bbox])
        elif isinstance(lt_obj, LTImage):
            rawdata = lt_obj.stream.get_rawdata()
            bs64data = base64.b64encode(rawdata).decode("utf-8")
            objects.append([f'<img src="data:image/jpeg;base64,{bs64data}" />', lt_obj.bbox])
        elif isinstance(lt_obj, LTFigure):
            objects.extend(parser_pdf_pages(lt_obj._objs))
    return objects

def get_pdf_contents(file, dirname=GUMMY_DIR):
    """Get PDF contents.

    Args:
        file (data, str) : url or path or data of PDF.
        dirname (str)    : if ``file`` is url, download and save it to ``dirname``. (defalt= ``GUMMY_DIR``)

    Returns:
        list : Each element is a list which contains [text, bbox(x0,y0,x1,y1)]
    """
    # Settings.
    rsrcmgr     = PDFResourceManager()
    laparams    = LAParams(detect_vertical=True)
    device      = PDFPageAggregator(rsrcmgr=rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr=rsrcmgr, device=device)
    #  parse PDF pages
    pdf_pages = []
    with get_pdf_pages(file=file, dirname=dirname) as pages:
        for page in pages:
            interpreter.process_page(page)
            layout = device.get_result()
            pdf_pages.append(parser_pdf_pages(layout_objs=layout._objs))
    return pdf_pages


# ========================================
# Below this, you need a library "PyPDF2" 
# ========================================

def createHighlight(bbox=(), contents="", color=[1,1,0], author="iwasakishuto(@cabernet_rock)"):
    from PyPDF2.generic import (DictionaryObject, NumberObject, FloatObject, NameObject, TextStringObject, ArrayObject)
    x1, y1, x2, y2 = bbox
    newHighlight = DictionaryObject()
    newHighlight.update({
        NameObject("/F")          : NumberObject(4),
        NameObject("/Type")       : NameObject("/Annot"),
        NameObject("/Subtype")    : NameObject("/Highlight"),
        NameObject("/T")          : TextStringObject(author),
        NameObject("/Contents")   : TextStringObject(contents),
        NameObject("/C")          : ArrayObject([FloatObject(c) for c in color]),
        NameObject("/Rect")       : ArrayObject([FloatObject(e) for e in bbox]),
        NameObject("/QuadPoints") : ArrayObject([FloatObject(e) for e in [x1,y2,x2,y2,x1,y1,x2,y1]]),
    })
    return newHighlight

def addHighlightToPage(highlight, page, output):
    from PyPDF2.generic import (NameObject, ArrayObject)
    highlight_ref = output._addObject(highlight)
    if "/Annots" in page:
        page[NameObject("/Annots")].append(highlight_ref)
    else:
        page[NameObject("/Annots")] = ArrayObject([highlight_ref])
