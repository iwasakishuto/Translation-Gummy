# coding: utf-8
import sys
import argparse
from selenium.webdriver.chrome.options import Options

from .models import TranslationGummy
from .utils._path import TEMPLATES_DIR
from .utils.driver_utils import get_chrome_options

def translate_journal(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(prog="gummy-journal", add_help=True)
    parser.add_argument("url", type=str, help="URL of a page you want to create a pdf.")
    parser.add_argument("-G", "--gateway",    type=str, default="useless", help="Gateway identifier, string name of a gateway")
    parser.add_argument("-T", "--translator", type=str, default="deepl",   help="Translator identifier, string name of a translator")
    parser.add_argument("-J", "--journal",    type=str, default=None,      help="Journal identifier, string name of a journal")
    # Chrome options
    parser.add_argument("--browser", action="store_true", help="Whether you want to run Chrome with GUI browser.")
    # PDF format
    parser.add_argument("-pdf", "--pdf-path", type=str, default=None, help="Path to output pdf file path.")
    parser.add_argument("-tpl", "--tpl-path", type=str, default=None, help="Path to template path.")
    parser.add_argument("--delete-html", action="store_false", help="Whether you want to delete an intermediate product (html)")
    args = parser.parse_args(argv)

    chrome_options = get_chrome_options(browser=args.browser)
    url = args.url
    gateway = args.gateway
    translator = args.translator
    journal_type = args.journal

    pdf_path = args.pdf_path
    tpl_path = args.tpl_path
    delete_html = args.delete_html
    if tpl_path is None:
        searchpath = TEMPLATES_DIR
        template = "paper.tpl"
    else:
        *searchpath, template = tpl_path.split("/")
        searchpath = "/".join(searchpath) or "."

    model = TranslationGummy(chrome_options=chrome_options, gateway=gateway, translator=translator)
    pdf_path = model.toPDF(
        url=url, path=pdf_path, journal_type=journal_type, gateway=gateway,
        searchpath=searchpath, template=template, delete_html=delete_html, 
    )
    return pdf_path

def translate_text(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(prog="gummy-translate", add_help=True)
    parser.add_argument("query", type=str, help="English to be translated")
    parser.add_argument("-T", "--translator", type=str, default="deepl",   help="Translator identifier, string name of a translator")
    parser.add_argument("--browser", action="store_true", help="Whether you want to run Chrome with GUI browser.")
    args = parser.parse_args(argv)

    chrome_options = get_chrome_options(browser=args.browser)
    query = args.query
    translator = args.translator

    model = TranslationGummy(chrome_options=chrome_options, gateway="useless", translator=translator)
    japanese = model.en2ja(query=query)
    return japanese
