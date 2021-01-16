# coding: utf-8
""" Utility programs for creating HTML or PDF."""
import os
import re
import warnings
import unicodedata
import pdfkit
from jinja2 import Environment, FileSystemLoader

from . import TEMPLATES_DIR
from .generic_utils import str_strip
from .coloring_utils import toRED, toBLUE, toGREEN

def sanitize_filename(fp, dirname=None, ext=None, allow_unicode=False):
    """Convert from original filename to sanitized filename

    Args:
        fp (str)             : File path.
        dirname (str)        : Directory part of the ``fp``
        ext (str)            : Required file extension.
        allow_unicode (bool) : Whether allowing unicode or not.

    Returns:
        str : Sanitized filename.

    Examples:
        >>> from gummy.utils import sanitize_filename
        >>> sanitize_filename("path/to/image\u2013.png")
        >>> 'path/to/image.png'
        >>> sanitize_filename("path/to/image\u2013.jpg", ext=".png")
        >>> 'path/to/image.jpg.png'
        >>> sanitize_filename("path/to/image\u2013.png", allow_unicode=True)
        >>> 'path/to/image–.png'
        >>> # Doesn't work
        >>> sanitize_filename(fp='mir-193 targets ALDH2 and contributes to toxic aldehyde accumulation and tyrosine hydroxylase dysfunction in cerebral ischemia/reperfusion injury')
        'mir-193 targets ALDH2 and contributes to toxic aldehyde accumulation and tyrosine hydroxylase dysfunction in cerebral ischemia/reperfusion injury'
        >>> # Work well :)
        >>> sanitize_filename(fp='mir-193 targets ALDH2 and contributes to toxic aldehyde accumulation and tyrosine hydroxylase dysfunction in cerebral ischemia/reperfusion injury', dirname=".")
        './mir-193 targets ALDH2 and contributes to toxic aldehyde accumulation and tyrosine hydroxylase dysfunction in cerebral ischemia0reperfusion injury'
    """
    if dirname is None:
        dirname, fn = os.path.split(fp)
    else:
        fn = os.path.relpath(fp, start=dirname)
    if allow_unicode:
        fn = unicodedata.normalize("NFKC", fn)
    else:
        fn = unicodedata.normalize("NFKD", fn).encode("ascii", "ignore").decode("ascii")
    fn = str_strip(fn)
    fn = re.sub(pattern=r'[\\\/\?\*\|<>":;]+', repl='', string=fn)
    if ext is not None:
        if not ext.startswith("."): ext = "." + ext
        if not fn.endswith(ext): fn += ext
    fp = os.path.normpath(os.path.join(dirname, fn))
    return fp

def get_jinja_all_attrs(string, keyname):
    """Get the keynames which each element in ``keyname`` is expected to have.

    Args:
        string (str)  : Content strings in template file.
        keyname (str) : keyname which is used in ``template.render(keyname=...)``

    Examples:
        >>> import os
        >>> from gummy.utils import TEMPLATES_DIR, get_jinja_all_attrs
        >>> path = os.path.join(TEMPLATES_DIR, "paper.html")
        >>> with open(path, mode="r", encoding="utf-8") as f:
        ...     html = "".join(f.readlines())
        >>> get_jinja_all_attrs(string=html, keyname="contents")
        {'en', 'head', 'img', 'ja', 'subhead'}
    """
    attributes = set()
    get_from_either_pipe = lambda x,y: x if len(x)>0 else y
    for arg in re.findall(pattern=r"{%\s+for\s+(.+)\s+in\s+" + keyname + r"\s+%}", string=string):
        # get 'bar' from {{ arg.bar }} or {{ arg['bar'] }}
        attrs = re.findall(pattern=rf"{{\s+{arg}(?:\.(.+?)|\[['\"](.+?)['\"]\])\s+}}", string=string)
        attrs = [get_from_either_pipe(*attr) for attr in attrs]
        attributes.update(attrs)
    return attributes

def check_contents(path, contents):
    """ Check whether all attributes in template is contained in contents.

    Args:
        path (str)     : path/to/template.file
        contens (list) : Each element in ``contents`` should be dictionary.
    """
    if (not isinstance(contents, list)) or \
        ((len(contents)>0) and (not isinstance(contents[0], dict))):
        raise TypeError("`contents` should be list, and each element in `contents` should be dictionary.")

    with open(path, mode="r", encoding="utf-8") as f:
        html = "".join(f.readlines())   
    # All attributes in template.
    attributes = get_jinja_all_attrs(string=html, keyname="contents")
    # All keys in contens list.
    content_keys = set([e for content in contents for e in content.keys()])
    
    # Print key which is in content_keys but not in attributes.
    for key in content_keys.difference(attributes):
        warnings.warn(f"An attribute {toGREEN(key)} is not used in {toBLUE(path)}.")
    # Print key which is in attributes but not in content_keys.
    for key in attributes.difference(content_keys):
        warnings.warn(f"An attribute {toGREEN(key)} is not used in this contents, but used in {toBLUE(path)}.")

def tohtml(path, title="", contents=[], searchpath=TEMPLATES_DIR, template="paper.html", verbose=True):
    """ Arrange ``title`` and ``contents`` in html format.

    Args:
        path (str)       : path/to/output.html
        title (str)      : title for html.
        contents (list)  : Contens which used for render method of ``jinja2.environment.Template`` instance.
        searchpath (str) : Loader will find templates from the file system, and this directory is a base.
        template (str)   : template filename. Loader will find ``f"{searchpath}/{template}"``
    
    Returns:
        str : path/to/output.html
    """
    env = Environment(loader=FileSystemLoader(searchpath=searchpath))
    template = env.get_template(template)

    # TODO: Check nested all variables.
    # check_contents(path=template.filename, contents=contents)
    
    root,ext = os.path.splitext(path)
    if ext == ".pdf":
        path = root + ".html"
    path = sanitize_filename(fp=path, ext=".html")
    with open(path, mode="w", encoding='utf-8') as f:
        output = template.render(title=title, contents=contents)
        try:
            f.write(output)
        except UnicodeEncodeError:
            f.write(output.encode("utf-8"))

    if verbose: print(f"Save HTML file at {toBLUE(path)}")
    return path

def html2pdf(path, delete_html=True, verbose=True, options={}):
    """Convert from HTML to PDF.

    Args:
        path (str)         : path/to/input.html
        delete_html (bool) : Whether you want to delete html file. (default= ``True``)
        verbose (bool)     : Whether to print message or not. (default= ``True``)
        options (dict)     : options for wkhtmltopdf. See https://wkhtmltopdf.org/usage/wkhtmltopdf.txt
    
    Returns:
        str : path/to/output.pdf
    """
    options.update({
        "page-size"           : "A4",
        "encoding"            : "UTF-8",
        # "quiet"               : not verbose,
        "header-html"         : os.path.join(TEMPLATES_DIR, "header.html"),
        # "include-in-outline"  : True,
        # "load-error-handling" : "ignore",
        # "footer-center"       : "Page  [page]  of  [toPage]",
        "--print-media-type" : None,
    })
    html_removed_path = path.replace(".html", "")
    pdf_path = html_removed_path + ".pdf"
    pdfkit.from_file(input=path, output_path=pdf_path, options=options)
    if verbose: print(f"Save PDF file at {toBLUE(pdf_path)}")
    if delete_html:
        os.remove(path)
        if verbose: print(f"Delete original HTML file at {toRED(path)}")
    return pdf_path

def toPDF(path, title="", contents=[], searchpath=TEMPLATES_DIR, template="paper.html", verbose=True, options={}):
    """ Arrange ``title`` and ``contents`` in html format, then convert it to PDF.

    Args:
        path (str)       : path/to/output.html
        title (str)      : title for html.
        contents (list)  : Contens which used for render method of ``jinja2.environment.Template`` instance.
        searchpath (str) : Loader will find templates from the file system, and this directory is a base.
        template (str)   : template filename. Loader will find ``f"{searchpath}/{template}"``
        verbose (bool)   : Whether to print message or not. (default= ``True``)
        options (dict)   : options for wkhtmltopdf. See https://wkhtmltopdf.org/usage/wkhtmltopdf.txt
    
    Returns:
        str : path/to/output.pdf
    """
    pdf_removed_path = path.remove(".pdf", "")
    html_path = pdf_removed_path + ".html"
    html_path = tohtml(path=html_path, title=title, contents=contents, searchpath=searchpath, template=template, verbose=verbose)
    pdf_path = html2pdf(path=html_path, delete_html=True, verbose=verbose, options=options)
    return pdf_path