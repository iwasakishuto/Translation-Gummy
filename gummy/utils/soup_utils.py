#coding: utf-8
import re
from bs4 import BeautifulSoup
from .generic_utils import str_strip

def str2soup(string):
    # string = string[string.find("<"):]
    soup = BeautifulSoup(markup=string, features="html5lib")
    for attr in ["html", "body", "head"]:
        if hasattr(soup, attr) and getattr(soup, attr) is not None:
            getattr(soup, attr).unwrap()
    return soup
    
def split_section(section, name=None, attrs={}, recursive=True, text=None, **kwargs):
    """ Split 'bs4.BeautifulSoup'.

    * Arguments *
    @params section       : A PageElement
    @params name          : A filter on tag name.
    @params attrs         : A dictionary of filters on attribute values.
    @params recursive     : If this is True, find() will perform a recursive 
                            search of this PageElement's children. Otherwise,
                            only the direct children will be considered.
    @params text          : 
    @params kwargs        : A dictionary of filters on attribute values.
    @return page_elements : A list of elements without filter tag elements.

    * Examples *
    <section>
      <h2></h2>
      <div>
        ~~~~~~~~                                       [ "<div>~~~~~~",
        <img>      --- split_section(name="img") --->    "<img>",
        ~~~~~~~~                                         "~~~~</div>"]
      </div>
    </section>
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
    """ Gouping 'bs4.BeautifulSoup' based on head.
    * Arguments * (Specify head)
    @params section       : A PageElement
    @params name          : A filter on tag name.
    @params attrs         : A dictionary of filters on attribute values.
    @params recursive     : If this is True, find() will perform a recursive 
                            search of this PageElement's children. Otherwise,
                            only the direct children will be considered.
    @params text          : 
    @params kwargs        : A dictionary of filters on attribute values.
    @return page_elements : A list of elements without filter tag elements.

    * Examples *

    <h2></h2>                                               <section>
    <div></div>                                               <h2></h2>
    <h2></h2>                                                 <div></div>   
    <div></div>   --- group_soup_with_head(name="h2") --->  </section>
    <h2></h2>                                               <section>
    <div></div>                                               <h2></h2>
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
    """
    Replace Old tag with New tag.
    ============================================================================
    How to find a old tags:
    @params old_name     : A filter on tag name.
    @params old_attrs    : A dictionary of filters on attribute values.
    @params old_recursive: If this is True, find_all() will perform a recursive search of this PageElement's children. Otherwise, only the direct children will be considered.
    @params old_limit    : Stop looking after finding this many results.
    @params old_kwargs   : A dictionary of filters on attribute values.
    ============================================================================
    How to freate a new Tags:
    @params new_name      : The name of the new Tag.
    @params new_namespace : The URI of the new Tag's XML namespace, if any.
    @params new_prefix    : The prefix for the new Tag's XML namespace, if any.
    @params new_attrs     : A dictionary of this Tag's attribute values; can be used instead of `kwattrs` for attributes like 'class' that are reserved words in Python.
    @params new_sourceline: The line number where this tag was (purportedly) found in its source document.
    @params new_sourcepos : The character position within `sourceline` where this tag was (purportedly) found.
    @params new_kwattrs   : Keyword arguments for the new Tag's attribute values.
    """
    for old in soup.find_all(name=old_name, attrs=old_attrs, recursive=old_recursive, text=old_text, limit=old_limit, **old_kwargs):
        new = BeautifulSoup(markup="", features="lxml").new_tag(name=new_name, namespace=new_namespace, nsprefix=new_nsprefix, attrs=new_attrs, sourceline=new_sourceline, sourcepos=new_sourcepos, **new_kwattrs)
        new.extend(list(old.children))
        old.replace_with(new)
    return soup

def find_target_text(soup, name=None, attrs={}, recursive=True, text=None, default="__NOT_FOUND__", strip=True, **kwargs):
    target = soup.find(name=name, attrs=attrs, recursive=recursive, text=text, **kwargs)
    if target is None:
        text = default
    else:
        text = target.text
    if strip:
        text = str_strip(string=text)
    return text

def find_target_id(soup, key, name=None, attrs={}, recursive=True, text=None, default=None, strip=True, **kwargs):
    target = soup.find(name=name, attrs=attrs, recursive=recursive, text=text, **kwargs)
    if target is None:
        id_ = default
    else:
        id_ = target.get(key=key, default=default)
    if strip:
        id_ = str_strip(string=text)
    return id_