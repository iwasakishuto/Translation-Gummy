# coding: utf-8
import urllib
import argparse
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from kerasy.utils import toBLUE, toGREEN
from kerasy.utils import ProgressMonitor

from .utils import get_driver

DEEPL_URL = "https://www.deepl.com/en/translator#en/ja/{query}"
DEEPL_CLASS_NAME = "lmt__translations_as_text__text_btn"

def en2ja(query, timeout=10, trials=3, verbose=1):
    url = DEEPL_URL.format(query=urllib.parse.quote(query))
    if verbose>0: print(f"query: {toBLUE(url)}")

    driver = get_driver()
    driver.get(url)

    monitor = ProgressMonitor(max_iter=trials, verbose=verbose, barname="DeepL")
    for i in range(trials):
        wait = WebDriverWait(driver, timeout=timeout)
        _ = wait.until(EC.presence_of_element_located((By.CLASS_NAME, DEEPL_CLASS_NAME)))
        html = driver.page_source.encode("utf-8")
        soup = BeautifulSoup(html, "lxml")
        ja = soup.find("button", class_=DEEPL_CLASS_NAME).text
        monitor.report(i, japanese=ja)
        if len(ja)>0:
            break
    monitor.remove()
    return ja


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--query",   type=str, required=True)
    parser.add_argument("--timeout",       type=int, default=10)
    parser.add_argument("--trials",        type=int, default=3)
    parser.add_argument("-v", "--verbose", type=int, default=1)
    args = parser.parse_args()

    query = args.query
    timeout = args.timeout
    trials = args.trials
    verbose = args.verbose

    japanese = en2ja(query=query, timeout=timeout, trials=trials, verbose=verbose)
    print(f"japanese:\n{toGREEN(japanese)}")