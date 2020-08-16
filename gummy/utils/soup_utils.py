#coding: utf-8
import re
from bs4 import BeautifulSoup
from .generic_utils import str_strip

def str2soup(string):
    # string = string[string.find("<"):]
    soup = BeautifulSoup(markup=string, features="lxml")
    for attr in ["html", "body"]:
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

def find_text(soup, name=None, attrs={}, recursive=True, text=None, not_found="[NOT FOUND]", strip=True, **kwargs):
    target = soup.find(name=name, attrs=attrs, recursive=recursive, text=text, **kwargs)
    if target is None:
        text = not_found
    else:
        text = target.text
    if strip:
        text = str_strip(string=text)
    return text