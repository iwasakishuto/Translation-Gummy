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


def translate_text(argv=sys.argv[1:]):
    """Translate from Japanese to English.

    Args:
        query (str)                 : English to be translated. (required)
        -T/--translator (str)       : Translator identifier, string name of a translator. (default= ``"deepl"`` )
        --browser (bool)            : Whether you want to run Chrome with GUI browser. (default= ``False`` )
        --quiet (bool)              : Whether you want to be quiet or not. (default= ``False`` )
        --translator-verbose (bool) : Whether you want to print translator's output or not. (default= ``False`` )

    Note:
        When you run from the command line, execute as follows::

        $ gummy-translate "This is a pen."

    Examples:
        >>> $ gummy-translate "This is a pen."
    """

    parser = argparse.ArgumentParser(prog="gummy-translate", add_help=True)
    parser.add_argument("query", type=str, help="English to be translated")
    parser.add_argument(
        "-T", "--translator", type=str, default="deepl", help="Translator identifier, string name of a translator"
    )
    parser.add_argument("--from-lang", type=str, default="en", help="Language before translation.")
    parser.add_argument("--to-lang", type=str, default="ja", help="Language after translation.")
    parser.add_argument("--browser", action="store_true", help="Whether you want to run Chrome with GUI browser.")
    parser.add_argument("--quiet", action="store_true", help="Whether you want to be quiet or not. (default=False)")
    parser.add_argument(
        "--quiet-translator",
        action="store_true",
        help="Whether you want translator to be quiet or not. (default=False)",
    )
    args = parser.parse_args(argv)

    chrome_options = get_chrome_options(browser=args.browser)
    query = args.query
    translator = args.translator
    from_lang = args.from_lang
    to_lang = args.to_lang
    verbose = not args.quiet
    translator_verbose = not args.quiet_translator

    model = TranslationGummy(
        chrome_options=chrome_options,
        gateway="useless",
        translator=translator,
        specialize=True,
        from_lang=from_lang,
        to_lang=to_lang,
        verbose=verbose,
        translator_verbose=translator_verbose,
    )
    japanese = model.translate(query=query)
    return japanese
