#coding: utf-8
import re
from bs4 import BeautifulSoup

def str2soup(string):
    string = re.sub(pattern=".*?(<[a-z].*)$", repl=r"\1", string=string)
    soup = BeautifulSoup(string, "lxml")
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
    page_elements = []
    while True:
        delimiter = section.find(name=name, attrs=attrs, recursive=recursive, text=text, **kwargs)
        if delimiter is None:
            if section is not None:
                page_elements.append(section)
            break
        str_delimiter = str(delimiter)
        f_element, *b_elements = str(section).split(sep=str_delimiter)
        f_element = re.sub(pattern="[ 　]+", repl=" ", string=f_element).strip()
        if len(f_element)>0:
            page_elements.append(str2soup(string=f_element))
        page_elements.append(delimiter)
        section = str2soup(string=str_delimiter.join(b_elements))
    return page_elements

def group_soup_with_head(soup, name=None, attrs={}, recursive=True, text=None, **kwargs):
    """ Gouping 'bs4.BeautifulSoup' based on head.
    # TODO: This is tooooo simple code, and `group_soup_with_head` is verrrry slow.

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
    sections = []
    num_sections = len(soup.find_all(name=name, attrs=attrs, recursive=recursive, text=text, **kwargs))
    if num_sections==0:
        section = BeautifulSoup(features="lxml").new_tag(name="section")
    for i in range(num_sections):
        headline = soup.find(name=name, attrs=attrs, recursive=recursive, text=text, **kwargs)
        str_headline = str(headline)
        f_element, *b_elements = str(soup).split(sep=str_headline)
        if i>0:
            content = str2soup(string=re.sub(pattern="[ 　]+", repl=" ", string=f_element))
            section.append(content)
            sections.append(section)
        section = BeautifulSoup(features="lxml").new_tag(name="section")
        section.append(headline)
        soup = str2soup(string=str_headline.join(b_elements))
    section.append(soup)
    sections.append(section)
    return sections

def find_text(soup, name=None, attrs={}, recursive=True, text=None, not_found="[NOT FOUND]", strip=True, **kwargs):
    target = soup.find(name=name, attrs=attrs, recursive=recursive, text=text, **kwargs)
    if target is None:
        text = not_found
    else:
        text = target.text
    if strip:
        text = text.strip()
    return text