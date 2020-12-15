#coding: utf-8
import re
from bs4 import BeautifulSoup
from .generic_utils import str_strip

def str2soup(string):
    """Convert strings to soup, and removed extra tags such as ``<html>``, ``<body>``, and ``<head>``.

    Args:
        string (str) : strings

    Returns:
        bs4.BeautifulSoup : A data structure representing a parsed HTML or XML document.

    Examples:
        >>> string = "<title>Translation-Gummy</title>"
        >>> type(string)
        str
        >>> soup = str2soup(string)
        >>> soup
        <title>Translation-Gummy</title>
        >>> type(soup)
        bs4.BeautifulSoup
        >>> from bs4 import BeautifulSoup
        >>> BeautifulSoup(string)
        <html><head><title>Translation-Gummy</title></head></html>
    """
    soup = BeautifulSoup(markup=string, features="html5lib")
    for attr in ["html", "body", "head"]:
        if hasattr(soup, attr) and getattr(soup, attr) is not None:
            getattr(soup, attr).unwrap()
    return soup
    
def split_section(section, name=None, attrs={}, recursive=True, text=None, **kwargs):
    """ Split ``bs4.BeautifulSoup``.

    Args:
        section (bs4.BeautifulSoup) : A data structure representing a parsed HTML or XML document.
        name (str)                  : A filter on tag name.
        attrs (dict)                : A dictionary of filters on attribute values.
        recursive (bool)            : If this is True, ``.find`` will perform a recursive search of this PageElement's children. Otherwise, only the direct children will be considered.
        text (str)                  : An inner text.
        kwargs (dict)               : A dictionary of filters on attribute values.
    
    Returns:
        list : A list of elements without filter tag elements.

    Examples:
        >>> from bs4 import BeautifulSoup
        >>> from gummy.utils import split_section
        >>> section = BeautifulSoup(\"\"\"
        ... <section>
        ...   <div>
        ...     <h2>Title</h2>
        ...     <div>
        ...     <p>aaaaaaaaaaaaaaaaaaaaaa</p>
        ...     <div>
        ...     <img/>
        ...     </div>
        ...     <p>bbbbbbbbbbbbbbbbbbbbbb</p>
        ...     </div>
        ...   </div>
        ... </section>
        >>> \"\"\")
        >>> len(split_section(section, name="img"))
        3
        >>> split_section(section, name="img")
        [<section>
        <div>
        <h2>Title</h2>
        <div>
        <p>aaaaaaaaaaaaaaaaaaaaaa</p>
        <div>
        </div></div></div></section>,
        <img/>,
        <p>bbbbbbbbbbbbbbbbbbbbbb</p>
        ]
    """
    str_section = str(section)
    page_elements = []
    delimiters = section.find_all(name=name, attrs=attrs, recursive=recursive, text=text, **kwargs)
    # Initialization (Prevent occuring an error when for-loop enter continue at the beginning (i=0))
    end = 0
    for i,delimiter in enumerate(delimiters):
        str_delimiter = str(delimiter)
        start = str_section.find(str_delimiter)
        if start==-1:
            continue
        page_elements.append(str2soup(string=str_section[end:start]))
        page_elements.append(delimiter)
        end = start + len(str_delimiter)
    page_elements.append(str2soup(string=str_section[end:]))
    return page_elements

def group_soup_with_head(soup, name=None, attrs={}, recursive=True, text=None, **kwargs):
    """ Gouping ``bs4.BeautifulSoup`` based on head.

    Args:
        section (bs4.BeautifulSoup) : A data structure representing a parsed HTML or XML document.
        name (str)                  : A filter on tag name.
        attrs (dict)                : A dictionary of filters on attribute values.
        recursive (bool)            : If this is True, ``.find`` will perform a recursive search of this PageElement's children. Otherwise, only the direct children will be considered.
        text (str)                  : An inner text.
        kwargs (dict)               : A dictionary of filters on attribute values.

    Returns:
        list : A list of elements without filter tag elements.

    Examples:
        >>> from bs4 import BeautifulSoup
        >>> from gummy.utils import group_soup_with_head
        >>> section = BeautifulSoup(\"\"\"
        ... <h2>AAA</h2>
        ... <div>
        ...   <p>aaaaaaaaaaaaaaaaaaaaaa</p>
        ... </div>
        ... <h2>BBB</h2>
        ... <div>
        ...   <p>bbbbbbbbbbbbbbbbbbbbbb</p>
        ... </div>
        >>> \"\"\")
        >>> sections = group_soup_with_head(section, name="h2")
        >>> len(sections)
        2
        >>> sections
        [<section><h2>AAA</h2><div>
        <p>aaaaaaaaaaaaaaaaaaaaaa</p>
        </div>
        </section>,
        <section><h2>BBB</h2><div>
        <p>bbbbbbbbbbbbbbbbbbbbbb</p>
        </div>
        </section>]
    """
    str_soup = str(soup)
    sections = []
    heads = soup.find_all(name=name, attrs=attrs, recursive=recursive, text=text, **kwargs)
    # Initialization (Prevent occuring an error when for-loop enter continue at the beginning (i=0))
    end = 0; section = BeautifulSoup(markup="", features="lxml").new_tag(name="section")
    if len(heads)>0:
        for i,head in enumerate(heads):
            str_head = str(head)
            start = str_soup.find(str_head)
            if start==-1:
                continue
            if i>0:
                body = str2soup(string=str_soup[end:start])
                section.append(body)
                sections.append(section)
            end = start + len(str_head)
            section = BeautifulSoup(markup="", features="lxml").new_tag(name="section")
            section.append(head)
        body = str2soup(string=str_soup[end:])
        section.append(body)
        sections.append(section)
    return sections

def replace_soup_tag(soup, 
    new_name, new_namespace=None, new_nsprefix=None, new_attrs={}, new_sourceline=None, 
    new_sourcepos=None, new_kwattrs={},
    old_name=None, old_attrs={}, old_recursive=True, old_text=None, old_limit=None, old_kwargs={}, **kwargs):
    """Replace Old tag with New tag.

    - Args named ``old_XXX`` specifies "How to find old tags"
    - Args named ``new_XXX`` specifies "How to create new tags"

    Args:
        old_name (str)       : A filter on tag name.
        old_attrs (dict)     : A dictionary of filters on attribute values.
        old_recursive (bool) : If this is True, ``.find_all`` will perform a recursive search of this PageElement's children. Otherwise, only the direct children will be considered.
        old_limit (int)      : Stop looking after finding this many results.
        old_kwargs (dict)    : A dictionary of filters on attribute values.
        new_name (str)       : The name of the new Tag.
        new_namespace (str)  : The URI of the new Tag's XML namespace, if any.
        new_prefix (str)     : The prefix for the new Tag's XML namespace, if any.
        new_attrs (dict)     : A dictionary of this Tag's attribute values; can be used instead of `kwattrs` for attributes like 'class' that are reserved words in Python.
        new_sourceline (str) : The line number where this tag was (purportedly) found in its source document.
        new_sourcepos (str)  : The character position within ``sourceline`` where this tag was (purportedly) found.
        new_kwattrs (dict)   : Keyword arguments for the new Tag's attribute values.
    
    Examples:
        >>> from bs4 import BeautifulSoup
        >>> from gummy.utils import replace_soup_tag
        >>> section = BeautifulSoup(\"\"\"
        ... <h2>AAA</h2>
        ... <div>
        ...   <p>aaaaaaaaaaaaaaaaaaaaaa</p>
        ... </div>
        ... <h3>BBB</h3>
        ... <div>
        ...   <p>bbbbbbbbbbbbbbbbbbbbbb</p>
        ... </div>
        >>> \"\"\")
        >>> section = replace_soup_tag(soup=section, old_name="h3", new_name="h2")
        >>> section
        <html><body><h2>AAA</h2>
        <div>
        <p>aaaaaaaaaaaaaaaaaaaaaa</p>
        </div>
        <h2>BBB</h2>
        <div>
        <p>bbbbbbbbbbbbbbbbbbbbbb</p>
        </div>
        </body></html>
    """
    for old in soup.find_all(name=old_name, attrs=old_attrs, recursive=old_recursive, text=old_text, limit=old_limit, **old_kwargs):
        new = BeautifulSoup(markup="", features="lxml").new_tag(name=new_name, namespace=new_namespace, nsprefix=new_nsprefix, attrs=new_attrs, sourceline=new_sourceline, sourcepos=new_sourcepos, **new_kwattrs)
        new.extend(list(old.children))
        old.replace_with(new)
    return soup

def find_target_text(soup, name=None, attrs={}, recursive=True, text=None, default="__NOT_FOUND__", strip=True, **kwargs):
    """Find target element, and get all child strings from it.

    Args:
        soup (bs4.BeautifulSoup) : A data structure representing a parsed HTML or XML document.
        name (str)               : A filter on tag name.
        attrs (dict)             : A dictionary of filters on attribute values.
        recursive (bool)         : If this is True, ``.find`` will perform a recursive search of this PageElement's children. Otherwise, only the direct children will be considered.
        text (str)               : An inner text.
        default (str)            : Default return value if element not found.
        strip (bool)             : Whether to use :func:`str_strip <gummy.utils.generic_utils.str_strip>`
        kwargs (dict)            : A dictionary of filters on attribute values.

    Returns:
        str : text

    Examples:
        >>> from bs4 import BeautifulSoup
        >>> from gummy.utils import find_target_text
        >>> section = BeautifulSoup(\"\"\"
        ... <h2>AAA</h2>
        ... <div> <p>aaaaaaaaaaaaaaaaaaaaaa</p></div>
        >>> \"\"\")
        >>> find_target_text(soup=section, name="div")
        'aaaaaaaaaaaaaaaaaaaaaa'
        >>> find_target_text(soup=section, name="div", strip=False)
        ' aaaaaaaaaaaaaaaaaaaaaa '
        >>> find_target_text(soup=section, name="divdiv", default="not found")
        'not found'
    """
    target = soup.find(name=name, attrs=attrs, recursive=recursive, text=text, **kwargs)
    if target is None:
        text = default
    else:
        text = target.text
    if strip:
        text = str_strip(string=text)
    return text

def find_all_target_text(soup, name=None, attrs={}, recursive=True, text=None, default="__NOT_FOUND__", strip=True, joint="", **kwargs):
    """Find target element, and get all child strings from it.

    Args:
        soup (bs4.BeautifulSoup) : A data structure representing a parsed HTML or XML document.
        name (str)               : A filter on tag name.
        attrs (dict)             : A dictionary of filters on attribute values.
        recursive (bool)         : If this is True, ``.find`` will perform a recursive search of this PageElement's children. Otherwise, only the direct children will be considered.
        text (str)               : An inner text.
        default (str)            : Default return value if element not found.
        strip (bool)             : Whether to use :func:`str_strip <gummy.utils.generic_utils.str_strip>`
        joint (str)              : Inserted between target strings.
        kwargs (dict)            : A dictionary of filters on attribute values.

    Returns:
        str : text

    Examples:
        >>> from bs4 import BeautifulSoup
        >>> from gummy.utils import find_all_target_text
        >>> section = BeautifulSoup(\"\"\"
        ... <div>
        ...   <p class="lang en">Hello</p>
        ...   <p class="lang zh-CN">你好</p>
        ...   <p class="lang es">Hola</p>
        ...   <p class="lang fr">Bonjour</p>
        ...   <p class="lang ja">こんにちは</p>
        ... </div>
        >>> \"\"\")
        >>> find_all_target_text(soup=section, name="p", class_="lang", joint=", ")
        'Hello, 你好, Hola, Bonjour, こんにちは'
        >>> find_all_target_text(soup=section, name="p", class_="es", joint=", ")
        'Hola'
    """
    texts = []
    for target in soup.find_all(name=name, attrs=attrs, recursive=recursive, text=text, **kwargs):
        text = target.text
        if strip:
            text = str_strip(string=text)
        texts.append(text)
    return joint.join(texts)

def find_target_id(soup, key, name=None, attrs={}, recursive=True, text=None, default=None, strip=True, **kwargs):
    """Find target element, and get id from it.

    Args:
        soup (bs4.BeautifulSoup) : A data structure representing a parsed HTML or XML document.
        key (str)                : id name.
        name (str)               : A filter on tag name.
        attrs (dict)             : A dictionary of filters on attribute values.
        recursive (bool)         : If this is True, ``.find`` will perform a recursive search of this PageElement's children. Otherwise, only the direct children will be considered.
        text (str)               : An inner text.
        default (str)            : Default return value if element not found.
        strip (bool)             : Whether to use :func:`str_strip <gummy.utils.generic_utils.str_strip>`
        kwargs (dict)            : A dictionary of filters on attribute values.

    Returns:
        str : text.

    Examples:
        >>> from bs4 import BeautifulSoup
        >>> from gummy.utils import find_target_id
        >>> section = BeautifulSoup(\"\"\"
        ... <h2>IMAGE</h2>
        ... <div>
        ...   <img id="apple-touch-icon" src="https://iwasakishuto.github.io/images/apple-touch-icon/Translation-Gummy.png">
        ... </div>
        >>> \"\"\")
        >>> find_target_id(soup=section, name="img", key="id")
        'apple-touch-icon'
        >>> find_target_id(soup=section, name="img", key="src")
        'https://iwasakishuto.github.io/images/apple-touch-icon/Translation-Gummy.png'
    """
    target = soup.find(name=name, attrs=attrs, recursive=recursive, text=text, **kwargs)
    if target is None:
        id_ = default
    else:
        id_ = target.get(key=key, default=default)
    if strip:
        id_ = str_strip(string=id_)
    return id_