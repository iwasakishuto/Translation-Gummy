# coding: utf-8
import os
import re
import bs4
import base64
import urllib

from ._path import IMG_NOT_FOUND_SRC
from .coloring_utils  import toBLUE, toGREEN, toRED
from .generic_utils import readable_size

CONTENT_ENCODING2EXT = {
    "x-gzip"                    : ".gz",
    "image/jpeg"                : ".jpg",
    "image/jpx"                 : ".jpx", 
    "image/png"                 : ".png",
    "image/gif"                 : ".gif",
    "image/webp"                : ".webp",
    "image/x-canon-cr2"         : ".cr2",
    "image/tiff"                : ".tif",
    "image/bmp"                 : ".bmp",
    "image/vnd.ms-photo"        : ".jxr",
    "image/vnd.adobe.photoshop" : ".psd",
    "image/x-icon"              : ".ico",
    "image/heic"                : ".heic",
}

CONTENT_TYPE2EXT = {
    "application/epub+zip"                  : ".epub",
    "application/zip"                       : ".zip",
    "application/x-tar"                     : ".tar",
    "application/x-rar-compressed"          : ".rar",
    "application/gzip"                      : ".gz",
    "application/x-bzip2"                   : ".bz2",
    "application/x-7z-compressed"           : ".7z",
    "application/x-xz"                      : ".xz",
    "application/pdf"                       : ".pdf",
    "application/x-msdownload"              : ".exe",
    "application/x-shockwave-flash"         : ".swf",
    "application/rtf"                       : ".rtf",
    "application/octet-stream"              : ".eot",
    "application/postscript"                : ".ps",
    "application/x-sqlite3"                 : ".sqlite",
    "application/x-nintendo-nes-rom"        : ".nes",
    "application/x-google-chrome-extension" : ".crx",
    "application/vnd.ms-cab-compressed"     : ".cab",
    "application/x-deb"                     : ".deb",
    "application/x-unix-archive"            : ".ar",
    "application/x-compress"                : ".Z",
    "application/x-lzip"                    : ".lz",
}


def decide_extension(content_encoding, content_type):
    """
    @params content_encoding :
    @return ext              :
    """
    ext = CONTENT_ENCODING2EXT.get(content_encoding) or CONTENT_TYPE2EXT.get(content_type) or ""
    return ext

def download_file(url, dirname=".", verbose=True):
    try:
        with urllib.request.urlopen(url) as web_file:
            # Get Information from webfile header
            headers = dict(web_file.headers._headers)
            content_encoding = headers.get('Content-Encoding')
            content_length   = readable_size(int(headers.get('Content-Length', '0')))
            content_type     = headers.get('Content-Type')
            # Decide extensions.
            ext = decide_extension(content_encoding, content_type) or ""
            path = os.path.join(dirname, url.split('/')[-1] + ext)
            if verbose:
                print(f"""Download source files from {toBLUE(url)}
                * Content-Encoding : {toGREEN(content_encoding)}
                * Content-Length   : {toGREEN(content_length)}
                * Content-Type     : {toGREEN(content_type)}
                * Save Destination : {toBLUE(path)} 
                """)
            data = web_file.read()
            with open(path, mode='wb') as local_file:
                local_file.write(data)
            return path
    except urllib.error.URLError as e:
        print(f"{toRED(e)} : url={toBLUE(url)}")

def src2base64(src, base=None):
    """ Create base64 encoded img tag.
    @params src : (str) image src url.
                  (bs4.element.Tag) <img> tag element.
    @params base: (str) base URL. 
                  Join a base URL and a possibly relative URL to form an 
                  absolute interpretation of the latter.
    """
    if isinstance(src, bs4.element.Tag) and src.name == "img":
        src = src.get("src", "")
    rela_url = re.sub(pattern=r"^(\/\/.*)$", repl=r"https:\1", string=src)
    url = urllib.parse.urljoin(base=base, url=rela_url)
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
