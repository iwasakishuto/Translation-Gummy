# coding: utf-8
import base64
import urllib
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTContainer, LTTextBox, LTImage, LTTextLine, LTFigure
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage

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

def getPDFPages(path):
    rsrcmgr     = PDFResourceManager()
    laparams    = LAParams(detect_vertical=True)
    device      = PDFPageAggregator(rsrcmgr=rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr=rsrcmgr, device=device)
    pdf_pages = []
    with open(path, 'rb') as f_pdf:
        pages = PDFPage.get_pages(f_pdf)
        for page in pages:
            interpreter.process_page(page)
            layout = device.get_result()
            pdf_pages.append(parser_pdf_pages(layout_objs=layout._objs))
    return pdf_pages
