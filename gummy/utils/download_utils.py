# coding: utf-8
import os
import re
import urllib
from kerasy.utils import toBLUE, toGREEN, toRED

def readable_size(size):
    for unit in ['K','M','G']:
        if abs(size) < 1024.0:
            break
        size /= 1024.0
    return f"{size:.2f} [{unit}B]"

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