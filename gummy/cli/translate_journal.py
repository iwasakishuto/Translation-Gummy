# coding: utf-8
"""CLI(Command Line Interface) tools

    Since the following two programs are frequently used, I created this file to be called from command line.

    - Translate your journals and generate a PDF.
    - Translation
"""
import argparse
import sys

from ..journals import SUPPORTED_CRAWL_TYPES
from ..models import TranslationGummy
from ..utils._path import TEMPLATES_DIR
from ..utils.driver_utils import get_chrome_options
from ..utils.generic_utils import DictParamProcessor, ListParamProcessorCreate


def translate_journal(argv=sys.argv[1:]):
    """Translate journals.

    Args:
        url (str)                   : URL of a paper or ``path/to/local.pdf``. (required)
        -G/--gateway (str)          : Gateway identifier, string name of a gateway. (default= ``"useless"`` )
        -T/--translator (str)       : Translator identifier, string name of a translator. (default= ``"deepl"`` )
        -J/--journal (str)          : Journal identifier, string name of a journal. (default= ``None`` )
        --crawl-type (str)          : Crawling type, if you not specify, use recommended crawling type. (default= ``None`` )
        -O/--out-dir (str)          : Where you want to save a created PDF. (default= ``GUMMY_DIR`` )
        --browser (bool)            : Whether you want to run Chrome with GUI browser. (default= ``False`` )
        -pdf/--pdf-path (str)       : Path to output pdf file path. (default= ``None`` )
        -tpl/--tpl-path (str)       : Path to template path. (default= ``None`` )
        --save-html (bool)          : Whether you want to save an intermediate html file. (default= ``False`` )
        --quiet (bool)              : Whether you want to be quiet or not. (default= ``False`` )
        --translator-verbose (bool) : Whether you want to print translator's output or not. (default= ``False`` )
        -GP/--gateway-params (dict) : Specify the value required to pass through the gateway. You can specify by ``-GP username=USERNAME -GP password=PASSWORD`` (default= ``{}`` )
        --highlight (bool)          : Whetehr you want to highlight the PDF or not. (default=False)")
        --ignore_length (int)       : If the number of English characters is smaller than ``ignore_length`` , do not highlight.
        --highlight_color (list)    : The highlight color.

    Note:
        When you run from the command line, execute as follows::

        $ gummy-journal "https://www.nature.com/articles/ncb0800_500"

    Examples:
        >>> $ gummy-journal "https://www.nature.com/articles/ncb0800_500"
    """
    parser = argparse.ArgumentParser(prog="gummy-journal", add_help=True)
    parser.add_argument("url", type=str, help="URL of a page you want to create a pdf.")
    parser.add_argument(
        "-G", "--gateway", type=str, default="useless", help="Gateway identifier, string name of a gateway"
    )
    parser.add_argument(
        "-T", "--translator", type=str, default="deepl", help="Translator identifier, string name of a translator"
    )
    parser.add_argument("-J", "--journal", type=str, default=None, help="Journal identifier, string name of a journal")
    parser.add_argument(
        "--crawl-type",
        type=str,
        default=None,
        help="Crawling type, if you not specify, use recommended crawling type.",
        choices=SUPPORTED_CRAWL_TYPES,
    )
    parser.add_argument("-O", "--out-dir", type=str, default=".", help="Where you want to save a created PDF.")
    parser.add_argument("--from-lang", type=str, default="en", help="Language before translation.")
    parser.add_argument("--to-lang", type=str, default="ja", help="Language after translation.")
    # Chrome options
    parser.add_argument("--browser", action="store_true", help="Whether you want to run Chrome with GUI browser.")
    # PDF format
    parser.add_argument("-pdf", "--pdf-path", type=str, default=None, help="Path to output pdf file path.")
    parser.add_argument("-tpl", "--tpl-path", type=str, default=None, help="Path to template path.")
    parser.add_argument(
        "--save-html", action="store_true", help="Whether you want to save an intermediate html file. (default=False)"
    )
    parser.add_argument("--quiet", action="store_true", help="Whether you want to be quiet or not. (default=False)")
    parser.add_argument(
        "--quiet-translator",
        action="store_true",
        help="Whether you want translator to be quiet or not. (default=False)",
    )
    parser.add_argument("--bulk", action="store_true", help="Whether to prioritize speed or readability.")
    # Gateway kwargs
    parser.add_argument(
        "-GP",
        "--gateway-params",
        default={},
        action=DictParamProcessor,
        help="Specify the value required to pass through the gateway. You can specify by -GP username=USERNAME -GP password=PASSWORD",
    )
    # Highlight
    parser.add_argument(
        "--highlight", action="store_true", help="Whetehr you want to highlight the PDF or not. (default=False)"
    )
    parser.add_argument(
        "--ignore-length",
        type=int,
        default=10,
        help="If the number of English characters is smaller than this value, do not highlight.",
    )
    parser.add_argument(
        "--highlight_color",
        action=ListParamProcessorCreate(type=float),
        default=[1, 1, 0],
        help="The highlight color.",
    )
    args = parser.parse_args(argv)

    chrome_options = get_chrome_options(browser=args.browser)
    url = args.url
    gateway = args.gateway
    translator = args.translator
    journal_type = args.journal
    crawl_type = args.crawl_type
    out_dir = args.out_dir
    from_lang = args.from_lang
    to_lang = args.to_lang
    correspond = not args.bulk
    pdf_path = args.pdf_path
    tpl_path = args.tpl_path
    delete_html = not args.save_html
    verbose = not args.quiet
    translator_verbose = not args.quiet_translator
    gateway_params = args.gateway_params
    highlight = args.highlight
    ignore_length = args.ignore_length
    highlight_color = args.highlight_color
    if tpl_path is None:
        searchpath = TEMPLATES_DIR
        template = "paper.html"
    else:
        *searchpath, template = tpl_path.split("/")
        searchpath = "/".join(searchpath) or "."

    model = TranslationGummy(
        chrome_options=chrome_options,
        gateway=gateway,
        translator=translator,
        specialize=True,
        from_lang=from_lang,
        to_lang=to_lang,
        verbose=verbose,
        translator_verbose=translator_verbose,
    )
    if highlight:
        pdf_path = model.highlight(
            url=url,
            path=pdf_path,
            out_dir=out_dir,
            journal_type=journal_type,
            gateway=gateway,
            ignore_length=ignore_length,
            highlight_color=highlight_color,
            **gateway_params,
        )
    else:
        pdf_path = model.toPDF(
            url=url,
            path=pdf_path,
            out_dir=out_dir,
            correspond=correspond,
            journal_type=journal_type,
            crawl_type=crawl_type,
            gateway=gateway,
            searchpath=searchpath,
            template=template,
            delete_html=delete_html,
            **gateway_params,
        )
    return pdf_path
