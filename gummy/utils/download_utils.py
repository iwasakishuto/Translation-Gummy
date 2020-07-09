# coding: utf-8
import os
import re
import bs4
import base64
import urllib
from kerasy.utils import toBLUE, toGREEN, toRED

from ._path import IMG_NOT_FOUND_SRC
from .generic_utils import readable_size

def decide_extension(content_encoding):
    """
    @params content_encoding :
    @return ext              :
    """
    ext = {
        "x-gzip"    : ".gz", # .tar.gz .tgz
        "image/png" : ".png",
    }.get(content_encoding, ".gzip")
    return ext

def download_file(url, dirname="."):
    try:
        with urllib.request.urlopen(url) as web_file:
            headers = dict(web_file.headers._headers)
            content_encoding = headers.get('Content-Encoding', 'x-gzip')
            content_length = readable_size(int(headers.get('Content-Length', '0')))
            content_type = headers.get('Content-Type', 'application/x-eprint-tar')
            ext = decide_extension(content_encoding)
            path = os.path.join(dirname, url.split('/')[-1] + ext)
            print(f"""Download source files from {toBLUE(url)}
            * Content-Encoding : {toGREEN(content_encoding)}
            * Content-Length   : {toGREEN(content_length)}
            * Content-Type     : {toGREEN(content_type)}
            * Save Destination : {toBLUE(path)} 
            """)
            data = web_file.read()
            with open(path, mode='wb') as local_file:
                local_file.write(data)
            return (path, content_encoding, ext)
    except urllib.error.URLError as e:
        print(toRED(e))

def src2base64(src):
    """ Create base64 encoded img tag.
    @params src : (str) image src url.
                  (bs4.element.Tag) <img> tag element.
    """
    if isinstance(src, bs4.element.Tag) and src.name == "img":
        src = src.get("src", "")
    url = re.sub(pattern=r"^(\/\/.*)$", repl=r"https:\1", string=src)
    try:
        with urllib.request.urlopen(url) as web_file:
            data = base64.b64encode(web_file.read()).decode('utf-8')
            img_tag = f'<img src="data:image/jpeg;base64,{data}" />'
    except urllib.error.URLError as e:
        print(toRED(e))
        img_tag = f'<img src="{IMG_NOT_FOUND_SRC}" />'
    return img_tag
    
def path2base64(path):
    """ Create base64 encoded img tag.
    @params path : (str) path/to/image.
    """
    try:
        with open(path, "r") as image_file:
            data = base64.b64encode(image_file.read()).decode('utf-8')
            img_tag = f'<img src="data:image/jpeg;base64,{data}" />'
    except:
        print(toRED(f"Could not load data from {toBLUE(path)}"))
        img_tag = f'<img src="{IMG_NOT_FOUND_SRC}" />'
    return img_tag
