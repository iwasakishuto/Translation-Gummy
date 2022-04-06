# coding: utf-8
"""Utility programs for handling and analyzing PDF file."""
import base64
import contextlib
import io
from io import _io
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTFigure, LTImage, LTItem, LTTextBox, LTTextLine
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from PyPDF2 import PdfFileWriter
from PyPDF2.generic import ArrayObject, DictionaryObject, FloatObject, NameObject, NumberObject, TextStringObject
from PyPDF2.pdf import PageObject
from werkzeug.datastructures import FileStorage

from ._path import GUMMY_DIR
from .download_utils import match2path


@contextlib.contextmanager
def get_pdf_pages(file: Union[FileStorage, str, _io._IOBase], dirname: str = GUMMY_DIR):
    """Get PDF pages.

    Args:
        file (data, str) : url or path or data of PDF.
        dirname (str)    : if ``file`` is url, download and save it to ``dirname``. (defalt= ``GUMMY_DIR``)
    """
    if isinstance(file, FileStorage) or isinstance(file, io.TextIOWrapper):
        yield PDFPage.get_pages(fp=file)
    else:
        path = match2path(file, dirname=dirname)
        with open(path, mode="rb") as f_pdf:
            yield PDFPage.get_pages(fp=f_pdf)


def parser_pdf_pages(layout_objs: List[LTItem]) -> List[Tuple[str, LTItem]]:
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


def get_pdf_contents(file: Union[FileStorage, str, _io._IOBase], dirname: str = GUMMY_DIR) -> List[Tuple[str, LTItem]]:
    """Get PDF contents.

    Args:
        file (data, str) : url or path or data of PDF.
        dirname (str)    : if ``file`` is url, download and save it to ``dirname``. (defalt= ``GUMMY_DIR``)

    Returns:
        list : Each element is a list which contains [text, bbox(x0,y0,x1,y1)]
    """
    # Settings.
    rsrcmgr = PDFResourceManager()
    laparams = LAParams(detect_vertical=True)
    device = PDFPageAggregator(rsrcmgr=rsrcmgr, laparams=laparams)
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


def createHighlight(
    bbox: Tuple[int, int, int, int] = (0, 0, 1, 1),
    contents: str = "",
    color: Tuple[int, int, int] = (1, 1, 0),
    author: str = "iwasakishuto(@cabernet_rock)",
):
    """Create a Highlight

    Args:
        bbox (tuple)   : a bounding box showing the location of highlight.
        contents (str) : Text comments for a highlight label.
        color (list)   : Highlight color. Defaults to ``[1,1,0]``. (yellow)
        author (str)   : Who wrote the annotation (comment). Defaults to ``"iwasakishuto(@cabernet_rock)"`` .

    Returns:
        DictionaryObject: Highlight information.

    Examples:
        >>> from gummy.utils import createHighlight, addHighlightToPage
        >>> from PyPDF2 import PdfFileWriter, PdfFileReader
        >>> page_no = 0
        >>> pdfOutput = PdfFileWriter()
        >>> with open("input.pdf", mode="rb") as inPdf:
        ...     pdfInput = PdfFileReader(inPdf)
        ...     page = pdfInput.getPage(page_no)
        ...     highlight = createHighlight(bbox=(10,10,90,90), contents="COMMENT", color=(1,1,0))
        ...     addHighlightToPage(highlight, page, pdfOutput)
        ...     pdfOutput.addPage(page)
        ...     with open("output.pdf", mode="wb") as outPdf:
        ...         pdfOutput.write(outPdf)
    """

    x1, y1, x2, y2 = bbox
    newHighlight = DictionaryObject()
    newHighlight.update(
        {
            NameObject("/F"): NumberObject(4),
            NameObject("/Type"): NameObject("/Annot"),
            NameObject("/Subtype"): NameObject("/Highlight"),
            NameObject("/T"): TextStringObject(author),
            NameObject("/Contents"): TextStringObject(contents),
            NameObject("/C"): ArrayObject([FloatObject(c) for c in color]),
            NameObject("/Rect"): ArrayObject([FloatObject(e) for e in bbox]),
            NameObject("/QuadPoints"): ArrayObject([FloatObject(e) for e in [x1, y2, x2, y2, x1, y1, x2, y1]]),
        }
    )
    return newHighlight


def addHighlightToPage(highlight: DictionaryObject, page: PageObject, output: PdfFileWriter):
    """Add a highlight to a page.

    Args:
        highlight (DictionaryObject) : Highlight information.
        page (PageObject)            : A single page within a PDF file.
        output (PdfFileWriter)       : A pdf writer.

    Examples:
        >>> from gummy.utils import createHighlight, addHighlightToPage
        >>> from PyPDF2 import PdfFileWriter, PdfFileReader
        >>> page_no = 0
        >>> pdfOutput = PdfFileWriter()
        >>> with open("input.pdf", mode="rb") as inPdf:
        ...     pdfInput = PdfFileReader(inPdf)
        ...     page = pdfInput.getPage(page_no)
        ...     highlight = createHighlight(bbox=(10,10,90,90), contents="COMMENT", color=(1,1,0))
        ...     addHighlightToPage(highlight, page, pdfOutput)
        ...     pdfOutput.addPage(page)
        ...     with open("output.pdf", mode="wb") as outPdf:
        ...         pdfOutput.write(outPdf)
    """
    highlight_ref = output._addObject(highlight)
    if "/Annots" in page:
        page[NameObject("/Annots")].append(highlight_ref)
    else:
        page[NameObject("/Annots")] = ArrayObject([highlight_ref])
