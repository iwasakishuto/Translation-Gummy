# coding: utf-8
"""This file defines a model that integrates all of :mod:`journals <gummy.journals>`,
:mod:`translators <gummy.translators>`, :mod:`gateways <gummy.gateways>`, and
it is possible to do all of the following at once.

1. Determine the ``journal_type`` of paper from the ``url`` or file extension.
2. If necessary, use a ``GummyGateway`` to access non-open content of the journal.
3. Parse the paper using ``GummyJournals`` and obtain the contents.
4. Translate the English obtained using ``GummyTranslators`` to Japanese.
5. Arrange Japanese and English according to the `templates <https://github.com/iwasakishuto/Translation-Gummy/tree/master/gummy/templates>`_ .
6. Convert the obtained HTML to PDF.

You can get (import) ``TranslationGummy`` by the following 2 ways.

.. code-block:: python

    >>> from gummy.models import TranslationGummy
    >>> from gummy import TranslationGummy
"""

import os
from typing import Any, Dict, Optional, Tuple, Union

from PyPDF2 import PdfFileReader, PdfFileWriter
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver

from gummy.utils.generic_utils import verbose2print

from . import gateways, journals, translators
from .utils._path import GUMMY_DIR, TEMPLATES_DIR
from .utils._type import T_PAPER_TITLE_CONTENTS
from .utils.coloring_utils import toACCENT, toBLUE
from .utils.download_utils import match2path
from .utils.driver_utils import get_driver
from .utils.journal_utils import whichJournal
from .utils.outfmt_utils import html2pdf, sanitize_filename, tohtml
from .utils.pdf_utils import addHighlightToPage, createHighlight


class TranslationGummy:
    """This class integrates all of the followings

    - :mod:`journals <gummy.journals>`
    - :mod:`translators <gummy.translators>`
    - :mod:`gateways <gummy.gateways>`

    Args:
        chrome_options (ChromeOptions)    : Instance of ChromeOptions. (default= :meth:`get_chrome_options() <gummy.utils.driver_utils.get_chrome_options>` )
        browser (bool)                    : Whether you want to run Chrome with GUI browser. (default= ``False`` )
        driver (WebDriver)                : Selenium WebDriver.
        gateway (str, GummyGateWay)       : identifier of the Gummy Gateway Class. See :mod:`gateways <gummy.gateways>`. (default= `"useless"`)
        translator (str, GummyTranslator) : identifier of the Gummy Translator Class. See :mod:`translators <gummy.translators>`. (default= `"deepl"`)
        maxsize (int)                     : Number of English characters that we can send a request at one time. (default= ``5000``)
        specialize (bool)                 : Whether to support multiple languages or specialize. (default= ``True``) If you want to specialize in translating between specific languages, set ``from_lang`` and ``to_lang`` arguments.
        from_lang (str)                   : Language before translation.
        to_lang (str)                     : Language after translation.
        verbose (bool)                    : Whether you want to print output or not. (default= ``True`` )
        translator_verbose (bool)         : Whether you want to print translator’s output or not. (default= ``False`` )
    """

    def __init__(
        self,
        chrome_options: Optional[Options] = None,
        browser: bool = False,
        undetected: bool = True,
        driver: Optional[WebDriver] = None,
        gateway: str = "useless",
        translator: str = "deepl",
        maxsize: int = 5000,
        specialize: bool = True,
        from_lang: str = "en",
        to_lang: str = "ja",
        verbose: bool = True,
        translator_verbose: bool = True,
    ):
        self.driver: WebDriver = driver or get_driver(
            chrome_options=chrome_options, browser=browser, undetected=undetected
        )
        self.gateway: str = gateway
        self.translator: translators.GummyAbstTranslator = translators.get(
            translator,
            maxsize=maxsize,
            specialize=specialize,
            from_lang=from_lang,
            to_lang=to_lang,
            verbose=translator_verbose,
        )
        self.verbose: bool = verbose
        self.print = verbose2print(verbose=verbose)

    def translate(
        self,
        query: str,
        barname: Optional[str] = None,
        from_lang: str = "en",
        to_lang: str = "ja",
        correspond: bool = False,
    ) -> str:
        """Translate English into Japanese. See :meth:`translate <gummy.translators.translate>`.

        Args:
            query (str)        : English to be translated.
            barname (str)      : Bar name for :meth:`ProgressMonitor <gummy.utils.monitor_utils.ProgressMonitor>`.
            from_lang (str)    : Language before translation.
            to_lang (str)      : Language after translation.
            correspond (bool)  : Whether to correspond the location of ``from_lang`` correspond to that of ``to_lang``.

        Examples:
            >>> from gummy import TranslationGummy
            >>> model = TranslationGummy()
            >>> ja = model.translate("This is a pen.")
            DeepLTranslator (query1) 03/30 [##------------------] 10.00% - 3.243[s]
            >>> print(ja)
            'これはペンです。'
        """
        return self.translator.translate(
            query=query,
            driver=self.driver,
            barname=barname,
            from_lang=from_lang,
            to_lang=to_lang,
            correspond=correspond,
        )

    def get_contents(
        self,
        url: str,
        journal_type: Optional[str] = None,
        crawl_type: Optional[str] = None,
        gateway: Optional[Union[str, gateways.GummyAbstGateWay]] = None,
        **gatewaykwargs,
    ) -> T_PAPER_TITLE_CONTENTS:
        """Get contents of the journal.

        Args:
            url (str)                   : URL of a paper or ``path/to/local.pdf``.
            journal_type (str)          : Journal type, if you not specify, judge by analyzing from ``url``.
            crawl_type (str)            : Crawling type, if you not specify, use recommended crawling type.
            gateway (str, GummyGateWay) : identifier of the Gummy Gateway Class. See :mod:`gateways <gummy.gateways>`. (default= ``None``)
            gatewaykwargs (dict)        : Gateway keywargs. See :meth:`passthrough <gummy.gateways.GummyAbstGateWay.passthrough>`.

        Returns:
            tuple (str, dict) : (title, content)

        Examples:
            >>> from gummy import TranslationGummy
            >>> model = TranslationGummy()
            >>> title, texts = model.get_contents("https://www.nature.com/articles/ncb0800_500")
            Estimated Journal Type : Nature
            Crawling Type: soup
                :
            >>> print(title)
            Formation of the male-specific muscle in female by ectopic expression
            >>> print(texts[:1])
            [{'head': 'Abstract', 'en': 'The  () gene product Fru has been ... for the sexually dimorphic actions of the gene.'}]
        """
        if journal_type is None:
            if os.path.exists(url):
                journal_type = "pdf"
            else:
                journal_type = whichJournal(url, driver=self.driver, verbose=self.verbose)
        gateway = gateway or self.gateway
        crawler = journals.get(journal_type, gateway=gateway, sleep_for_loading=3, verbose=self.verbose)
        title, texts = crawler.get_contents(url=url, driver=self.driver, crawl_type=crawl_type, **gatewaykwargs)
        return (title, texts)

    def toHTML(
        self,
        url: str,
        path: Optional[str] = None,
        out_dir: str = GUMMY_DIR,
        from_lang: str = "en",
        to_lang: str = "ja",
        correspond: bool = True,
        journal_type: Optional[str] = None,
        crawl_type: Optional[str] = None,
        gateway: Optional[Union[str, gateways.GummyAbstGateWay]] = None,
        searchpath: str = TEMPLATES_DIR,
        template: str = "paper.html",
        **gatewaykwargs,
    ):
        """Get contents from URL and create a HTML.

        Args:
            url (str)                   : URL of a paper or ``path/to/local.pdf``.
            path/out_dir (str)          : Where you save a created HTML. If path is None, save at ``<out_dir>/<title>.html`` (default= ``GUMMY_DIR``)
            from_lang (str)             : Language before translation.
            to_lang (str)               : Language after translation.
            correspond (bool)           : Whether to correspond the location of ``from_lang`` correspond to that of ``to_lang``.
            journal_type (str)          : Journal type, if you specify, use ``journal_type`` journal crawler. (default= `None`)
            crawl_type (str)            : Crawling type, if you not specify, use recommended crawling type. (default= `None`)
            gateway (str, GummyGateWay) : identifier of the Gummy Gateway Class. See :mod:`gateways <gummy.gateways>`. (default= `None`)
            searchpath/template (str)   : Use a ``<searchpath>/<template>`` tpl for creating HTML. (default= `TEMPLATES_DIR/paper.html`)
            gatewaykwargs (dict)        : Gateway keywargs. See :meth:`passthrough <gummy.gateways.GummyAbstGateWay.passthrough>`.
        """
        title, contents = self.get_contents(
            url=url, journal_type=journal_type, crawl_type=crawl_type, gateway=gateway, **gatewaykwargs
        )
        self.print(f"\nTranslation: {toACCENT(self.translator.name)}\n{'='*30}")
        len_contents = len(contents)
        # Combine split text for faster translation.
        if crawl_type == "pdf":
            raw: str = ""
            for i, content in enumerate(contents):
                barname = f"[{i+1:>0{len(str(len_contents))}}/{len_contents}] " + toACCENT(content.get("head", "\t"))
                if "body" in content:
                    if content["body"]["raw"] == "":
                        content["body"]["raw"], content["body"]["translated"] = self.translator.translate_wrapper(
                            query=raw, barname=barname, from_lang=from_lang, to_lang=to_lang, correspond=correspond
                        )
                        raw = ""
                    else:
                        raw += " " + content["body"].pop("raw")
                elif "img" in content:
                    self.print(barname + "<img>")
                    if "caption" in content["img"]:
                        (
                            content["img"]["caption"]["raw"],
                            content["img"]["caption"]["translated"],
                        ) = self.translator.translate_wrapper(
                            query=content["img"]["caption"]["raw"],
                            barname=barname,
                            from_lang=from_lang,
                            to_lang=to_lang,
                            correspond=correspond,
                        )
            if len(raw) > 0:
                content["body"]["raw"], content["body"]["translated"] = self.translator.translate_wrapper(
                    query=raw, barname=barname, from_lang=from_lang, to_lang=to_lang, correspond=correspond
                )
        else:
            for i, content in enumerate(contents):
                barname = f"[{i+1:>0{len(str(len_contents))}}/{len_contents}] " + toACCENT(content.get("head", "\t"))
                if "body" in content:
                    content["body"]["raw"], content["body"]["translated"] = self.translator.translate_wrapper(
                        query=content["body"]["raw"],
                        barname=barname,
                        from_lang=from_lang,
                        to_lang=to_lang,
                        correspond=correspond,
                    )
                elif "img" in content:
                    self.print(barname + "<img>")
                    if "caption" in content["img"]:
                        (
                            content["img"]["caption"]["raw"],
                            content["img"]["caption"]["translated"],
                        ) = self.translator.translate_wrapper(
                            query=content["img"]["caption"]["raw"],
                            barname=barname,
                            from_lang=from_lang,
                            to_lang=to_lang,
                            correspond=correspond,
                        )
        if path is None:
            path = os.path.join(out_dir, sanitize_filename(fp=title, dirname="."))
        htmlpath = tohtml(
            path=path, title=title, contents=contents, searchpath=searchpath, template=template, verbose=self.verbose
        )
        return htmlpath

    def toPDF(
        self,
        url: str,
        path: Optional[str] = None,
        out_dir: str = GUMMY_DIR,
        from_lang: str = "en",
        to_lang: str = "ja",
        correspond: bool = True,
        journal_type: Optional[str] = None,
        crawl_type: Optional[str] = None,
        gateway: Optional[Union[str, gateways.GummyAbstGateWay]] = None,
        searchpath: str = TEMPLATES_DIR,
        template: str = "paper.html",
        delete_html: bool = True,
        options: Dict[str, Any] = {},
        **gatewaykwargs,
    ):
        """Get contents from URL and create a PDF.

        Args:
            url (str)                   : URL of a paper or ``path/to/local.pdf``.
            path/out_dir (str)          : Where you save a created HTML. If path is None, save at ``<out_dir>/<title>.html`` (default= ``GUMMY_DIR``)
            from_lang (str)             : Language before translation.
            to_lang (str)               : Language after translation.
            correspond (bool)           : Whether to correspond the location of ``from_lang`` correspond to that of ``to_lang``.
            journal_type (str)          : Journal type, if you specify, use ``journal_type`` journal crawler. (default= `None`)
            crawl_type (str)            : Crawling type, if you not specify, use recommended crawling type. (default= `None`)
            gateway (str, GummyGateWay) : identifier of the Gummy Gateway Class. See :mod:`gateways <gummy.gateways>`. (default= `None`)
            searchpath/template (str)   : Use a ``<searchpath>/<template>`` tpl for creating HTML. (default= `TEMPLATES_DIR/paper.html`)
            delete_html (bool)          : Whether you want to delete an intermediate html file. (default= `True`)
            options (dict)              : Options for wkhtmltopdf. See https://wkhtmltopdf.org/usage/wkhtmltopdf.txt (default= `{}`)
            gatewaykwargs (dict)        : Gateway keywargs. See :meth:`passthrough <gummy.gateways.GummyAbstGateWay.passthrough>`.
        """
        htmlpath = self.toHTML(
            url=url,
            path=path,
            out_dir=out_dir,
            from_lang=from_lang,
            to_lang=to_lang,
            correspond=correspond,
            journal_type=journal_type,
            crawl_type=crawl_type,
            gateway=gateway,
            searchpath=searchpath,
            template=template,
            **gatewaykwargs,
        )
        self.print(f"\nConvert from HTML to PDF\n{'='*30}")
        pdfpath = html2pdf(path=htmlpath, delete_html=delete_html, verbose=self.verbose, options=options)
        return pdfpath

    def highlight(
        self,
        url: str,
        path: Optional[str] = None,
        out_dir: str = GUMMY_DIR,
        from_lang: str = "en",
        to_lang: str = "ja",
        journal_type: Optional[str] = None,
        gateway: Optional[Union[str, gateways.GummyAbstGateWay]] = None,
        ignore_length: int = 10,
        highlight_color: Tuple[int, int, int] = (1, 1, 0),
        **gatewaykwargs,
    ):
        """Get contents from URL and create a PDF.

        Args:
            url (str)                   : URL of a paper or ``path/to/local.pdf``.
            path/out_dir (str)          : Where you save a created HTML. If path is None, save at ``<out_dir>/<title>.html`` (default= ``GUMMY_DIR``)
            from_lang (str)             : Language before translation.
            to_lang (str)               : Language after translation.
            journal_type (str)          : Journal type, if you specify, use ``journal_type`` journal crawler. (default= `None`)
            gateway (str, GummyGateWay) : identifier of the Gummy Gateway Class. See :mod:`gateways <gummy.gateways>`. (default= `None`)
            ignore_length (int)         : If the number of English characters is smaller than ``ignore_length`` , do not highlight
            highlight_color (list)      : The highlight color.
            gatewaykwargs (dict)        : Gateway keywargs. See :meth:`passthrough <gummy.gateways.GummyAbstGateWay.passthrough>`.
        """
        title, contents = self.get_contents(
            url=url, journal_type=journal_type, crawl_type="pdf", gateway=gateway, **gatewaykwargs
        )
        path_ = match2path(url, dirname=out_dir)
        out_path = path or os.path.join(out_dir, "_higlighted".join(os.path.splitext(os.path.basename(path_))))
        with open(path_, "rb") as inPdf:
            pdfInput = PdfFileReader(inPdf)
            pdfOutput = PdfFileWriter()
            page_no = 0
            page = None
            len_contents = len(contents)
            for i, content in enumerate(contents):
                if "head" in content:
                    if page_no > 0:
                        pdfOutput.addPage(page)
                    page = pdfInput.getPage(page_no)
                    page_no += 1
                raw = content.get("raw", "")
                if raw == "" or len(raw) < ignore_length:
                    continue
                barname = f"[page.{page_no} {i+1:>0{len(str(len_contents))}}/{len_contents}] "
                translated = self.translator.translate(
                    query=raw, barname=barname, from_lang=from_lang, to_lang=to_lang, correspond=False
                )
                highlight = createHighlight(bbox=content["bbox"], contents=translated, color=highlight_color)
                addHighlightToPage(highlight, page, pdfOutput)
            pdfOutput.addPage(page)
            with open(out_path, "wb") as outPdf:
                pdfOutput.write(outPdf)
            self.print(f"{toBLUE(out_path)} is created.")
        return out_path
