# coding: utf-8
import time
import urllib
import argparse
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from kerasy.utils import toBLUE, toGREEN
from kerasy.utils import ProgressMonitor

if __package__ is None and __name__ == "__main__":
    from utils import get_driver
else:
    from .utils import get_driver

DEEPL_URL = "https://www.deepl.com/en/translator#en/ja/{query}"
DEEPL_CLASS_NAME = "lmt__translations_as_text__text_btn"

def deepl_en2ja(driver, query, maxsize=5000, timeout=1, trials=10, verbose=1):
    japanese = []
    len_query = len(query)
    num_query = (len_query-1)//maxsize+1
    for i in range(num_query):
        q = query[i*maxsize: (i+1)*maxsize]
        url = DEEPL_URL.format(query=urllib.parse.quote(q))
        if verbose>0: 
            print(f"query: {toBLUE(url)}")
        driver.get(url)

        monitor = ProgressMonitor(max_iter=trials, verbose=verbose, barname=f"DeepL query no.{i+1}")
        for i in range(trials):
            time.sleep(timeout)
            html = driver.page_source.encode("utf-8")
            soup = BeautifulSoup(html, "lxml")
            ja = soup.find("button", class_=DEEPL_CLASS_NAME).text
            monitor.report(i, japanese=ja)
            if len(ja)>0: break
        monitor.remove()
        japanese.append(ja)
    
    japanese = "".join(japanese)
    return japanese

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--query",   type=str, required=True)
    parser.add_argument("--timeout",       type=int, default=1)
    parser.add_argument("--trials",        type=int, default=10)
    parser.add_argument("-v", "--verbose", type=int, default=1)
    args = parser.parse_args()

    query = args.query
    timeout = args.timeout
    trials = args.trials
    verbose = args.verbose

    with get_driver() as driver:
        japanese = deepl_en2ja(driver=driver, query=query, timeout=timeout, trials=trials, verbose=verbose)
    print(f"japanese:\n{toGREEN(japanese)}")