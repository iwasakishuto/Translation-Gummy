# coding: utf-8
import os
import time
from bs4 import BeautifulSoup
from kerasy.utils import toGREEN, toBLUE

from .utils import pass_gate_way
from .utils import load_environ

def get_from_nature(url, driver, sleep_for_loading=5, need_gateway=True):
    is_ok = load_environ()
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
    for decoTag in soup(["script", "style", "meta", "link", "noscript", "i", "sup"]):
        decoTag.decompose()
    sections = soup.find_all("section")

    texts = []
    for section in sections:
        headline = section.get("aria-labelledby")
        if headline in [None, "Bib1", "author-information", "ethics", "additional-information", "rightslink", "article-info", "further-reading", "article-comments"]:
            continue
        text = section.get_text()
        print(f"{toGREEN(headline)} : {section.get_text()[:10]}...")
        texts.append([headline, text])

    return title, texts
