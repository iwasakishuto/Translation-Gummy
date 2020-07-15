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
    
def split_soup(soup, name="img"):
    """
    @params soup          : A PageElement
    @params name          : A filter on tag name.
    @return page_elements : A list of elements without filter tag elements.
    @return delimiters    : A list of filter tag elements.
    """
    page_elements = []
    while True:
        delimiter = soup.find(name=name)
        if delimiter is None:
            if soup is not None:
                page_elements.append(soup)
            break
        str_delimiter = str(delimiter)
        f_element, *b_elements = str(soup).split(sep=str_delimiter)
        f_element = re.sub(pattern="[ 　]+", repl=" ", string=f_element).strip()
        if len(f_element)>0:
            page_elements.append(str2soup(string=f_element))
        page_elements.append(delimiter)
        soup = str2soup(string=str_delimiter.join(b_elements))
    return page_elements

def split_soup_sections(soup_sections, name="img"):
    splitted_soup_sections = []
    for section in soup_sections:
        splitted_soup_sections.extend(split_soup(soup=section, name=name))
    return splitted_soup_sections

def split_soup_by_name(soup, name="h2", attrs={}, recursive=True, text=None, **kwargs):
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