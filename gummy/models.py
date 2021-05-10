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
import time

from . import gateways
from . import journals
from . import translators

from .utils._path import GUMMY_DIR, TEMPLATES_DIR
from .utils.coloring_utils import toACCENT, toBLUE, toGREEN
from .utils.driver_utils import get_driver
from .utils.journal_utils import whichJournal
from .utils.outfmt_utils import tohtml, html2pdf, sanitize_filename
from .utils.download_utils import match2path
from .utils.driver_utils import get_driver
from .utils.pdf_utils import createHighlight, addHighlightToPage

class TranslationGummy():
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
    def __init__(self, chrome_options=None, browser=False, driver=None, 
                 gateway="useless", translator="deepl", maxsize=5000, 
                 specialize=True, from_lang="en", to_lang="ja",
                 verbose=True, translator_verbose=True):
        self.driver = driver or get_driver(chrome_options=chrome_options, browser=browser)
        self.gateway = gateway
        self.translator = translators.get(translator, maxsize=maxsize, specialize=specialize, from_lang=from_lang, to_lang=to_lang, verbose=translator_verbose)
        self.verbose = verbose

    def translate(self, query, barname=None, from_lang="en", to_lang="ja", correspond=False):
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
        return self.translator.translate(query=query, driver=self.driver, barname=barname, from_lang=from_lang, to_lang=to_lang, correspond=correspond)

    def get_contents(self, url, journal_type=None, crawl_type=None, gateway=None, **gatewaykwargs):
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
        return title, texts

    def toHTML(self, url, path=None, out_dir=GUMMY_DIR,
               from_lang="en", to_lang="ja", correspond=True,
               journal_type=None, crawl_type=None, gateway=None,
               searchpath=TEMPLATES_DIR, template="paper.html", 
               **gatewaykwargs):
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
            url=url, journal_type=journal_type, crawl_type=crawl_type, 
            gateway=gateway, **gatewaykwargs
        )
        print(f"\nTranslation: {toACCENT(self.translator.name)}\n{'='*30}")
        len_contents = len(contents)
        # Combine split text for faster translation.
        if crawl_type=="pdf":
            raw = ""
            for i,content in enumerate(contents):
                barname = f"[{i+1:>0{len(str(len_contents))}}/{len_contents}] " + toACCENT(content.get("head","\t"))            
                if "raw" in content:
                    if content["raw"]=="":
                        content["raw"], content["translated"] = self.translator.translate_wrapper(query=raw, barname=barname, from_lang=from_lang, to_lang=to_lang, correspond=correspond)
                        raw = ""
                    else:
                        raw += " "+content.pop("raw")
                elif "img" in content and self.verbose:
                    print(barname + "<img>")
            if len(raw)>0:
                content["raw"], content["translated"] = self.translator.translate_wrapper(query=raw, barname=barname, from_lang=from_lang, to_lang=to_lang, correspond=correspond)
        else:
            for i,content in enumerate(contents):
                barname = f"[{i+1:>0{len(str(len_contents))}}/{len_contents}] " + toACCENT(content.get("head","\t"))            
                if "raw" in content:
                    content["raw"], content["translated"] = self.translator.translate_wrapper(query=content["raw"], barname=barname, from_lang=from_lang, to_lang=to_lang, correspond=correspond)
                elif "img" in content and self.verbose:
                    print(barname + "<img>")
        if path is None:
            path = os.path.join(out_dir, sanitize_filename(fp=title, dirname="."))
        htmlpath = tohtml(
            path=path, title=title, contents=contents, 
            searchpath=searchpath, template=template, verbose=self.verbose
        )
        return htmlpath

    def toPDF(self, url, path=None, out_dir=GUMMY_DIR,
              from_lang="en", to_lang="ja", correspond=True,
              journal_type=None, crawl_type=None, gateway=None, 
              searchpath=TEMPLATES_DIR, template="paper.html",
              delete_html=True, options={}, 
              **gatewaykwargs):
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
            url=url, path=path, out_dir=out_dir,
            from_lang=from_lang, to_lang=to_lang, correspond=correspond,
            journal_type=journal_type, crawl_type=crawl_type, gateway=gateway, 
            searchpath=searchpath, template=template,
            **gatewaykwargs
        )
        if self.verbose: print(f"\nConvert from HTML to PDF\n{'='*30}")
        pdfpath = html2pdf(path=htmlpath, delete_html=delete_html, verbose=self.verbose, options=options)
        return pdfpath

    def highlight(self, url, path=None, out_dir=GUMMY_DIR,
                  from_lang="en", to_lang="ja", journal_type=None, gateway=None, 
                  ignore_length=10, highlight_color=[1,1,0],
                  **gatewaykwargs):
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
        from PyPDF2 import PdfFileWriter, PdfFileReader
        title, contents = self.get_contents(
            url=url, journal_type=journal_type, crawl_type="pdf", 
            gateway=gateway, **gatewaykwargs
        )
        path_ = match2path(url, dirname=out_dir)
        out_path = path or os.path.join(out_dir, "_higlighted".join(os.path.splitext(os.path.basename(path_))))
        with open(path_, "rb") as inPdf:
            pdfInput  = PdfFileReader(inPdf)
            pdfOutput = PdfFileWriter()
            page_no = 0
            len_contents = len(contents)
            for i,content in enumerate(contents):
                if "head" in content:
                    if page_no>0: 
                        pdfOutput.addPage(page)
                    page = pdfInput.getPage(page_no)
                    page_no += 1
                raw = content.get("raw", "")
                if raw=="" or len(raw)<ignore_length: continue
                barname = f"[page.{page_no} {i+1:>0{len(str(len_contents))}}/{len_contents}] "            
                translated = self.translator.translate(query=raw, barname=barname, from_lang=from_lang, to_lang=to_lang, correspond=False)
                highlight = createHighlight(bbox=content["bbox"], color=highlight_color, contents=translated)
                addHighlightToPage(highlight, page, pdfOutput)
            pdfOutput.addPage(page)
            with open(out_path, "wb") as outPdf:
                pdfOutput.write(outPdf)
            print(f"{toBLUE(out_path)} is created.")
        return out_path