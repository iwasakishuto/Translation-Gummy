# coding: utf-8
import sys
import argparse
from selenium.webdriver.chrome.options import Options

from .models import TranslationGummy
from .journals import SUPPORTED_CRAWL_TYPES
from .utils._path import TEMPLATES_DIR, GUMMY_DIR
from .utils.driver_utils import get_chrome_options
from .utils.generic_utils import MonoParamProcessor

def translate_journal(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(prog="gummy-journal", add_help=True)
    parser.add_argument("url", type=str, help="URL of a page you want to create a pdf.")
    parser.add_argument("-G", "--gateway",    type=str, default="useless", help="Gateway identifier, string name of a gateway")
    parser.add_argument("-T", "--translator", type=str, default="deepl",   help="Translator identifier, string name of a translator")
    parser.add_argument("-J", "--journal",    type=str, default=None,      help="Journal identifier, string name of a journal")
    parser.add_argument("--crawl-type",       type=str, default=None,      help="Crawling type, if you not specify, use recommended crawling type.", choices=SUPPORTED_CRAWL_TYPES)
    parser.add_argument("-O", "--out-dir",    type=str, default=GUMMY_DIR, help="Where you want to save a created PDF.")
    # Chrome options
    parser.add_argument("--browser", action="store_true", help="Whether you want to run Chrome with GUI browser.")
    # PDF format
    parser.add_argument("-pdf", "--pdf-path", type=str, default=None, help="Path to output pdf file path.")
    parser.add_argument("-tpl", "--tpl-path", type=str, default=None, help="Path to template path.")
    parser.add_argument("--save-html",          action="store_true",  help="Whether you want to delete an intermediate html file. (default=True)")
    parser.add_argument("--quiet",              action="store_true",  help="Whether you want to be quiet or not. (default=False)")
    parser.add_argument("--translator-verbose", action="store_true",  help="Whether you want to print translator's output or not. (default=False)")
    # Gateway kwargs
    parser.add_argument("-GP", "--gateway-params", default={}, action=MonoParamProcessor, help="Specify the value required to pass through the gateway. You can specify by -GP username=USERNAME -GP password=PASSWORD")
    args = parser.parse_args(argv)

    chrome_options = get_chrome_options(browser=args.browser)
    url = args.url
    gateway = args.gateway
    translator = args.translator
    journal_type = args.journal
    crawl_type = args.crawl_type
    out_dir = args.out_dir

    pdf_path = args.pdf_path
    tpl_path = args.tpl_path
    delete_html = not args.save_html
    verbose = not args.quiet
    translator_verbose = args.translator_verbose
    gateway_params = args.gateway_params
    if tpl_path is None:
        searchpath = TEMPLATES_DIR
        template = "paper.tpl"
    else:
        *searchpath, template = tpl_path.split("/")
        searchpath = "/".join(searchpath) or "."

    model = TranslationGummy(
        chrome_options=chrome_options, gateway=gateway, translator=translator, 
        verbose=verbose, translator_verbose=translator_verbose,
    )
    pdf_path = model.toPDF(
        url=url, path=pdf_path, out_dir=out_dir,
        journal_type=journal_type, crawl_type=crawl_type, gateway=gateway,
        searchpath=searchpath, template=template, 
        delete_html=delete_html, **gateway_params,
    )
    return pdf_path

def translate_text(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(prog="gummy-translate", add_help=True)
    parser.add_argument("query", type=str, help="English to be translated")
    parser.add_argument("-T", "--translator", type=str, default="deepl",   help="Translator identifier, string name of a translator")
    parser.add_argument("--browser", action="store_true", help="Whether you want to run Chrome with GUI browser.")
    parser.add_argument("--quiet",              action="store_true",  help="Whether you want to be quiet or not. (default=False)")
    parser.add_argument("--translator-verbose", action="store_true",  help="Whether you want to print translator's output or not. (default=False)")
    args = parser.parse_args(argv)

    chrome_options = get_chrome_options(browser=args.browser)
    query = args.query
    translator = args.translator
    verbose = not args.quiet
    translator_verbose = args.translator_verbose

    model = TranslationGummy(
        chrome_options=chrome_options, gateway="useless", translator=translator,
        verbose=verbose, translator_verbose=translator_verbose,
    )
    japanese = model.en2ja(query=query)
    return japanese
