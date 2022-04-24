# coding: utf-8
""" Utility programs for downloading """
import base64
import os
import re
import urllib
from io import _io
from typing import Dict, Optional, Union

import bs4

from ._path import GUMMY_DIR, IMG_NOT_FOUND_SRC
from .coloring_utils import toBLUE, toGREEN, toRED
from .compress_utils import extract_from_compressed, is_compressed
from .driver_utils import download_PDF_with_driver
from .generic_utils import readable_bytes
from .monitor_utils import progress_reporthook_create

CONTENT_ENCODING2EXT: Dict[str, str] = {
    "x-gzip": ".gz",
    "image/jpeg": ".jpg",
    "image/jpx": ".jpx",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/x-canon-cr2": ".cr2",
    "image/tiff": ".tif",
    "image/bmp": ".bmp",
    "image/vnd.ms-photo": ".jxr",
    "image/vnd.adobe.photoshop": ".psd",
    "image/x-icon": ".ico",
    "image/heic": ".heic",
}

CONTENT_TYPE2EXT: Dict[str, str] = {
    "application/epub+zip": ".epub",
    "application/zip": ".zip",
    "application/x-tar": ".tar",
    "application/x-rar-compressed": ".rar",
    "application/gzip": ".gz",
    "application/x-bzip2": ".bz2",
    "application/x-7z-compressed": ".7z",
    "application/x-xz": ".xz",
    "application/pdf": ".pdf",
    "application/x-msdownload": ".exe",
    "application/x-shockwave-flash": ".swf",
    "application/rtf": ".rtf",
    "application/octet-stream": ".eot",
    "application/postscript": ".ps",
    "application/x-sqlite3": ".sqlite",
    "application/x-nintendo-nes-rom": ".nes",
    "application/x-google-chrome-extension": ".crx",
    "application/vnd.ms-cab-compressed": ".cab",
    "application/x-deb": ".deb",
    "application/x-unix-archive": ".ar",
    "application/x-compress": ".Z",
    "application/x-lzip": ".lz",
}


def decide_extension(
    content_encoding: Optional[str] = None, content_type: Optional[str] = None, filename: Optional[str] = None
) -> str:
    """Decide File Extension based on ``content_encoding`` and ``content_type``
    Args:
        content_encoding (str) : The MIME type of the resource or the data.
        content_type (str)     : The Content-Encoding entity header is used to compress the media-type.
        filename (str)         : The filename.

    Returns:
        ext (str): Starts with "."

    Examples:
        >>> from gummy.utils import decide_extension
        >>> decide_extension(content_encoding="x-gzip", content_type="application/zip")
        .gz
        >>> decide_extension(content_encoding="image/png", content_type=None)
        .png
        >>> decide_extension(content_encoding=None, content_type="application/pdf")
        .pdf
    """
    ext = (
        CONTENT_ENCODING2EXT.get(content_encoding)
        or CONTENT_TYPE2EXT.get(content_type)
        or "." + str(filename).split(".")[-1]
    )
    return ext


def download_file(
    url: str, dirname: str = ".", path: Optional[str] = None, bar_width: int = 20, verbose: bool = True
) -> str:
    """Download a file.
    Args:
        url (str)       : File URL.
        dirname (str)   : The directory where downloaded data will be saved.
        path (str)      : path/to/downloaded_file
        bar_width (int) : The width of progress bar.
        verbose (bool)  : Whether print verbose or not.

    Returns:
        path (str) : path/to/downloaded_file

    Examples:
        >>> from gummy.utils import download_file
        >>> download_file(url="https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_eye.xml")
        Download a file from https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_eye.xml
                    * Content-Encoding : None
                    * Content-Length   : (333.404296875, 'MB')
                    * Content-Type     : text/plain; charset=utf-8
                    * Save Destination : ./haarcascade_eye.xml
        haarcascade_eye.xml	100.0%[####################] 0.1[s] 5.5[GB/s]	eta -0.0[s]
        './haarcascade_eye.xml'
    """
    try:
        with urllib.request.urlopen(url) as web_file:
            # Get Information from webfile header
            headers = dict(web_file.headers._headers)
        content_encoding = headers.get("Content-Encoding")
        content_length, unit = readable_bytes(int(headers.get("Content-Length", 0)))
        content_length = f"{content_length:.1f} [{unit}]"
        content_type = headers.get("Content-Type")
        fn = url.split("/")[-1]
        if path is None:
            *name, ext = fn.split(".")
            name = ".".join(name)
            guessed_ext = decide_extension(content_encoding, content_type, fn)
            path = os.path.join(dirname, name + guessed_ext)
        if verbose:
            print(
                f"""Download a file from {toBLUE(url)}
            * Content-Encoding : {toGREEN(content_encoding)}
            * Content-Length   : {toGREEN(content_length)}
            * Content-Type     : {toGREEN(content_type)}
            * Save Destination : {toBLUE(path)}"""
            )
        _, res = urllib.request.urlretrieve(
            url=url,
            filename=path,
            reporthook=progress_reporthook_create(filename=fn, bar_width=bar_width, verbose=verbose),
        )
    except urllib.error.URLError as e:
        if verbose:
            print(f"{toRED(e)} : url={toBLUE(url)}")
            print(f"Try to download using webdriver {toRED('(Open Browser)')}")
        try:
            path = download_PDF_with_driver(url=url, dirname=dirname, verbose=verbose)
        except urllib.error.URLError as e:
            print(f"{toRED(e)}")
            path = None
    return path


def src2base64(src: Union[bs4.element.Tag, str], base: Optional[str] = None) -> str:
    """Create base64 encoded img tag from src url or <img> tag element.

    Args:
        src (str, bs4.element.Tag) : Image src url, or ``<img>`` tag element.
        base (str)                 : Base URL. Join a base URL and a possibly relative URL to form an absolute interpretation of the latter.

    Returns:
        str : base64 encoded img tag

    Examples:
        >>> from gummy.utils import src2base64
        >>> img_tag = src2base64(src="https://iwasakishuto.github.io/images/apple-touch-icon/Translation-Gummy.png")
        >>> with open("sample.html", mode="w") as f:
        ...     f.write(img_tag)
        >>> # open sample.html to check the results.
        >>> img_tag = src2base64(src="https://iwasakishuto.github.io/images/XXX/XXXXX.png")
        Tried to get an image but got an error: HTTP Error 404: Not Found
        >>> with open("error.html", mode="w") as f:
        ...     f.write(img_tag)
        >>> # open sample.html to check the results.
    """
    if isinstance(src, bs4.element.Tag) and src.name == "img":
        for target in ["src", "data-src", "data-original"]:
            s = src.get(target)
            if (s is not None) and (not re.match(pattern=r"^(javascript:|data:).+", string=s)):
                break
        src = s
    url = urllib.parse.urljoin(base=base, url=src)
    try:
        request = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0"}
        )
        with urllib.request.urlopen(request) as web_file:
            data = base64.b64encode(web_file.read()).decode("utf-8")
            img_tag = f'<img src="data:image/jpeg;base64,{data}"/>'
    except Exception as e:
        print(f"Tried to get an image but got an error: {toRED(e)}")
        img_tag = f'<img src="{IMG_NOT_FOUND_SRC}"/>'
    return img_tag


def path2base64(path: str) -> str:
    """Create base64 encoded img tag from local image.

    Args:
        path (str) : path/to/image.

    Returns:
        str : base64 encoded img tag

    Examples:
        >>> from gummy.utils import path2base64, download_file
        >>> path = download_file(url="https://iwasakishuto.github.io/images/apple-touch-icon/Translation-Gummy.png")
        Download a file from https://iwasakishuto.github.io/images/apple-touch-icon/Translation-Gummy.png
                    * Content-Encoding : None
                    * Content-Length   : 21.4 [MB]
                    * Content-Type     : image/png
                    * Save Destination : ./Translation-Gummy.png
        Translation-Gummy.png	100.0%[####################] 0.0[s] 3.4[GB/s]	eta -0.0[s]
        >>> img_tag = path2base64(path=path)
        >>> with open("sample.html", mode="w") as f:
        ...     f.write(img_tag)
        >>> # open sample.html to check the results.
    """
    try:
        with open(path, "rb") as image_file:
            data = base64.b64encode(image_file.read()).decode("utf-8")
            img_tag = f'<img src="data:image/jpeg;base64,{data}"/>'
    except Exception as e:
        print(toRED(f"[{str(e)}]\nCould not load data from {toBLUE(path)}"))
        img_tag = f'<img src="{IMG_NOT_FOUND_SRC}" />'
    return img_tag


def match2path(file: Union[str, _io._IOBase], dirname: str = GUMMY_DIR) -> str:
    """Match url or path to path while downloading if ``file`` is url.

    Args:
        file (str) : url or path or data of PDF.
        dirname (str)    : if ``file`` is url, download and save it to ``dirname``. (defalt= ``GUMMY_DIR``)

    Returns:
        str : path to a PDF.
    """
    if isinstance(file, str) and (not os.path.exists(file)):
        path = download_file(url=file, dirname=dirname)
        if path is None:
            print(toRED(f"Failed to download PDF from {toBLUE(file)}"))
        ext = "." + path.split(".")[-1]
        if is_compressed(ext):
            extracted_file_paths = extract_from_compressed(path, ext=".pdf", dirname=dirname)
            path = extracted_file_paths[0]
    else:
        path = file
    return path
