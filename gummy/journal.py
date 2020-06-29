# coding: utf-8
import re
import os
import time
from bs4 import BeautifulSoup
from kerasy.utils import toGREEN, toBLUE

from .utils import DOWNLOAD_DIR
from .utils.gateway_utils import pass_gate_way
from .utils.environ_utils import load_environ
from .utils.download_utils import download_file, decide_extension
from .utils.compress_utils import extract_from_compressed, is_compressed

DecomposeTagDefaults = ["script", "style", "meta", "link", "noscript", "i", "sup"]
NATURE_AVOID_LIST = ["Bib1", "author-information", "ethics", "additional-information", "rightslink", "article-info", "further-reading", "article-comments"]

def get_from_nature(url, driver, sleep_for_loading=5, need_gateway=True):
    _ = load_environ()
    if need_gateway:
        driver = pass_gate_way(
            driver = driver,
            url = os.getenv("TRANSLATION_GUMMY_GATEWAY_URL"),
            submit = "btnSubmit_6",
            confirm = "btnContinue",
            username = os.getenv("TRANSLATION_GUMMY_GATEWAY_USERNAME"),
            password = os.getenv("TRANSLATION_GUMMY_GATEWAY_PASSWORD"),
        )
    driver.get(url)
    print(f"Get {toBLUE(url)}\nNow loading...")
    time.sleep(sleep_for_loading)

    html = driver.page_source.encode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find(name="h1", attrs={"class" : "c-article-title"}).text
    for decoTag in soup(DecomposeTagDefaults):
        decoTag.decompose()
    sections = soup.find_all("section")

    texts = []
    for section in sections:
        aria_labelledby = section.get("aria-labelledby")
        if aria_labelledby is None or aria_labelledby in NATURE_AVOID_LIST:
            continue
        h2Tag = section.find_all("h2")
        headline = h2Tag[0] if len(h2Tag)>0 else aria_labelledby
        text = section.get_text()
        if text.startswith(headline):
            text = text.lstrip(headline)
        print(f"{toGREEN(headline)} : {section.get_text()[:10]}...")
        texts.append([headline, text])

    return title, texts

def get_from_arxiv(url, driver=None, need_gateway=False):
    source_href = re.sub(pattern=r".*?\/?(\d+\.\d+)", repl=r"https://arxiv.org/e-print/\1", string=url)
    path, _, ext = download_file(source_href, dirname=DOWNLOAD_DIR)
    if is_compressed(ext):
        extracted_file_paths = extract_from_compressed(path, ext=".tex", dirname=DOWNLOAD_DIR)
        return extracted_file_paths


    