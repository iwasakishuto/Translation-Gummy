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
from .download_utils import download_file

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
        if isinstance(file, str) and (not os.path.exists(file)):
            path = download_file(url=file, dirname=dirname)
            if path is None:
                print(toRED(f"Failed to download PDF from {toBLUE(file)}"))
            ext = "." + path.split(".")[-1]
            if is_compressed(ext):
                extracted_file_paths = extract_from_compressed(path, ext=".pdf", dirname=dirname)
                path = extracted_file_paths[0]
        else:
            path = file
        with open(path, mode="rb") as f_pdf:
            yield PDFPage.get_pages(fp=f_pdf)

def parser_pdf_pages(layout_objs):
    """Parse PDF pages and get contents in order.

    Args:
        layout_objs (list) : Each element is pdfminer.layout object.

    Returns:
        texts (list) : Each element is text (str).
    """
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

def get_pdf_contents(file, dirname=GUMMY_DIR):
    """Get PDF contents.

    Args:
        file (data, str) : url or path or data of PDF.
        dirname (str)    : if ``file`` is url, download and save it to ``dirname``. (defalt= ``GUMMY_DIR``)
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
