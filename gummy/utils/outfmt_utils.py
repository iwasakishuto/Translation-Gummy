# coding: utf-8
import os
import re
import warnings
import pdfkit
from jinja2 import Environment, FileSystemLoader

from . import TEMPLATES_DIR
from .coloring_utils import toRED, toBLUE, toGREEN

def sanitize_filename(fn, ext=None):
    fn = fn.replace("/", "√")
    if ext is not None:
        ext = ext if ext.startswith(".") else "."+ext
        if not fn.endswith(ext):
            fn += ext
    return fn

def get_jinja_all_attrs(string, argname):
    attributes = set()
    get_from_either_pipe = lambda x,y: x if len(x)>0 else y
    for arg in re.findall(pattern=r"{%\s+for\s+(.+)\s+in\s+" + argname + r"\s+%}", string=string):
        # get 'bar' from {{ arg.bar }} or {{ arg['bar'] }}
        attrs = re.findall(pattern=rf"{{\s+{arg}(?:\.(.+?)|\[['\"](.+?)['\"]\])\s+}}", string=string)
        attrs = [get_from_either_pipe(*attr) for attr in attrs]
        attributes.update(attrs)
    return attributes

def check_contents(path, contents):
    """ Check whether all attributes in template is contained in contents.
    @params path    : (str)  path/to/template.file
    @params contens : (list) contens[i] is dict.
    """
    if (not isinstance(contents, list)) or ((len(contents)>0) and (not isinstance(contents[0], dict))):
        raise TypeError("`contents` should be list, and each element in `contents` should be dictionary.")

    with open(path, mode="r") as f:
        html = "".join(f.readlines())   
    # All attributes in template.
    attributes = get_jinja_all_attrs(string=html, argname="contents")
    # All keys in contens list.
    content_keys = set([e for content in contents for e in content.keys()])
    for key in content_keys.difference(attributes):
        warnings.warn(f"An attribute {toGREEN(key)} is not used in {toBLUE(path)}.")
    for key in attributes.difference(content_keys):
        warnings.warn(f"An attribute {toGREEN(key)} is not used in this contents, but used in {toBLUE(path)}.")

def tohtml(path, title="", contents=[], searchpath=TEMPLATES_DIR, template="paper.tpl", verbose=True):
    """ Convert title and contents to html format.
    @params path       : path/to/html.
    @params title      : title for html.
    @params contents   : Contens which used for render method of `jinja2.environment.Template` instance.
    @params searchpath : Loader will find templates from the file system, and this directory is a base.
    @params template   : template filename. Loader will find searchpath/template.
    @return path       : path/to/html.
    """
    env = Environment(loader=FileSystemLoader(searchpath=searchpath))
    template = env.get_template(template)

    check_contents(path=template.filename, contents=contents)
      
    with open(path, mode="w") as f:
        f.write(template.render(title=title, contents=contents))
    if verbose: print(f"Save HTML file at {toBLUE(path)}")
    return path

def html2pdf(path, delete_html=True, verbose=True, options={}):
    """
    @params path        : path/to/html
    @params delete_html : Whether you want to delete html file.
    @params options     : options for wkhtmltopdf. See 'https://wkhtmltopdf.org/usage/wkhtmltopdf.txt'
    @return pdf_path    : path/to/pdf
    """
    options.update({
        "page-size"           : "A4",
        "encoding"            : "UTF-8",
        "quiet"               : not verbose,
        "header-html"         : os.path.join(TEMPLATES_DIR, "header.html"),
        # "include-in-outline"  : True,
        # "load-error-handling" : "ignore",
        # "footer-center"       : "Page  [page]  of  [toPage]",
    })
    html_removed_path = path.replace(".html", "")
    pdf_path = html_removed_path + ".pdf"
    pdfkit.from_file(input=path, output_path=pdf_path, options=options)
    if verbose: print(f"Save PDF file at {toBLUE(pdf_path)}")
    if delete_html:
        os.remove(path)
        if verbose: print(f"Delete original HTML file at {toRED(path)}")
    return pdf_path

def toPDF(path, title="", contents=[], searchpath=TEMPLATES_DIR, template="paper.tpl", verbose=True, options={}):
    """ Convert title and contents to PDF format.
    @params path       : path/to/pdf.
    @params title      : title for html.
    @params contents   : Contens which used for render method of `jinja2.environment.Template` instance.
    @params searchpath : Loader will find templates from the file system, and this directory is a base.
    @params template   : template filename. Loader will find searchpath/template.
    @params options    : options for wkhtmltopdf. See 'https://wkhtmltopdf.org/usage/wkhtmltopdf.txt'
    @return path       : path/to/pdf.
    """
    pdf_removed_path = path.remove(".pdf", "")
    html_path = pdf_removed_path + ".html"
    html_path = tohtml(path=html_path, title=title, contents=contents, searchpath=searchpath, template=template, verbose=verbose)
    pdf_path = html2pdf(path=html_path, delete_html=True, verbose=verbose, options=options)
    return pdf_path