# Translation Gummy

![header](https://github.com/iwasakishuto/Translation-Gummy/blob/master/image/header.png?raw=true)
[![PyPI version](https://badge.fury.io/py/Translation-Gummy.svg)](https://pypi.org/project/Translation-Gummy/)
[![GitHub version](https://badge.fury.io/gh/iwasakishuto%2FTranslation-Gummy.svg)](https://github.com/iwasakishuto/Translation-Gummy)
![Python package](https://github.com/iwasakishuto/Translation-Gummy/workflows/Python%20package/badge.svg)
![Upload Python Package](https://github.com/iwasakishuto/Translation-Gummy/workflows/Upload%20Python%20Package/badge.svg)
[![license](https://img.shields.io/github/license/mashape/apistatus.svg?maxAge=2592000)](https://github.com/iwasakishuto/Translation-Gummy/blob/master/LICENSE)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/iwasakishuto/Translation-Gummy/blob/master/examples/Colaboratory.ipynb)
[![Docker file](https://img.shields.io/badge/%F0%9F%90%B3-Dockerfile-0db7ed?style=flat-radius)](https://github.com/iwasakishuto/Translation-Gummy/blob/master/docker/Dockerfile)
[![Documentation](https://img.shields.io/badge/Documentation-portfolio-001d34?style=flat-radius)](https://iwasakishuto.github.io/Translation-Gummy/index.html)
[![twitter badge](https://img.shields.io/badge/twitter-Requests-1da1f2?style=flat-radius&logo=twitter)](https://www.twitter.com/messages/compose?recipient_id=1042783905697288193&text=Please%20support%20this%20journal%3A%20)
[![Qiita badge1](https://img.shields.io/badge/「ほん訳コンニャク」を食べて論文を読もう-Qiita-64c914?style=flat-radius)](https://qiita.com/cabernet_rock/items/670d5cd597bcd9f2ff3f)
[![Qiita badge2](https://img.shields.io/badge/「ほん訳コンニャク」を使ってみよう。-Qiita-64c914?style=flat-radius)](https://qiita.com/cabernet_rock/items/1f9bff5e0b9363da312d)
[![website](https://img.shields.io/badge/website-Translation--Gummy-lightblue)](https://elb.translation-gummy.com/)
[![Sponsor](https://img.shields.io/badge/%E2%9D%A4-Sponsor-db61a2)](https://github.com/sponsors/iwasakishuto)
[![Add to Slack](https://platform.slack-edge.com/img/add_to_slack.png)](https://elb.translation-gummy.com/slack_auth_begin)

**Translation Gummy** is a **_magical gadget_** which enables user to be able to speak and understand other languages. **※ Supported journals are listed [here](https://github.com/iwasakishuto/Translation-Gummy/wiki/Supported-journals).**

## Installation

1. Install **`Translation-Gummy`** (There are two ways to install):
    - **Install from PyPI (recommended):**
        ```sh
        $ sudo pip install Translation-Gummy
        ```
   - **Alternatively: install `Translation-Gummy` from the GitHub source:**
       ```sh
       $ git clone https://github.com/iwasakishuto/Translation-Gummy.git
       # If you want to use the latest version (under development)
       $ git clone -b develop https://github.com/iwasakishuto/Translation-Gummy.git
       $ cd Translation-Gummy
       $ sudo python setup.py install
       ```
2. Install **`wkhtmltopdf`**
   - **Debian/Ubuntu:**
        ```sh
        $ sudo apt-get install wkhtmltopdf
        ```
    - **macOS:**
        ```sh
        $ brew install homebrew/cask/wkhtmltopdf
        ```
3. Install **driver** for `selenium`:
**`Selenium`** requires a driver to interface with the chosen browser, so please visit the [documentation](https://selenium-python.readthedocs.io/installation.html#drivers) to install it.
    ```sh
    # Example: Chrome
    # visit "chrome://settings/help" to check your chrome version.
    # visit "https://chromedriver.chromium.org/downloads" to check <Suitable.Driver.Version> for your chrome.
    $ wget https://chromedriver.storage.googleapis.com/<Suitable.Driver.Version>/chromedriver_mac64.zip
    $ unzip chromedriver_mac64.zip
    $ mv chromedriver /usr/local/bin/chromedriver
    $ chmod +x /usr/local/bin/chromedriver
    ```

※ See [![Docker file](https://img.shields.io/badge/%F0%9F%90%B3-Dockerfile-0db7ed?style=flat-radius)](https://github.com/iwasakishuto/Translation-Gummy/blob/master/docker/Dockerfile) or [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/iwasakishuto/Translation-Gummy/blob/master/examples/Colaboratory.ipynb) for more specific example.

## Quick example

- **[example notebooks](https://nbviewer.jupyter.org/github/iwasakishuto/Translation-Gummy/blob/master/examples/)**
- **Translation**:
    - **Python Module:**
    ```python
    >>> from gummy import TranslationGummy
    >>> model = TranslationGummy(translator="deepl", from_lang="en", to_lang="ja")
    [success] local driver can be built.
    [failure] remote driver can't be built.
    DRIVER_TYPE: local
    >>> model.en2ja("This is a pen.")
    DeepLTranslator (query1) 02/30[#-------------------]  6.67% - 2.144[s]   translated: これはペン
    'これはペンです。'
    ```
    - **Command line:**
    ```sh
    $ gummy-translate "This is a pen." --from-lang en --to-lang ja
    [success] local driver can be built.
    [failure] remote driver can't be built.
    DRIVER_TYPE: local
    DeepLTranslator (query1) 02/30[#-------------------]  6.67% - 2.185[s]   translated: これはペン
    これはペンです。
    ```
    - **Output**
    ![gummy-translate](https://github.com/iwasakishuto/Translation-Gummy/blob/master/image/demo.gummy-translate.gif?raw=true)
- **Create PDF (with translation)**
    - **Python Module:**
    ```python
    >>> from gummy import TranslationGummy
    >>> model = TranslationGummy(gateway="utokyo", translator="deepl")
    >>> pdfpath = model.toPDF(url="https://www.nature.com/articles/ncb0800_500", delete_html=True)
    ```
    - **Command line:**
    ```sh
    $ gummy-journal "https://www.nature.com/articles/ncb0800_500"
    ```
    - **Output**
    ![gummy-journal](https://github.com/iwasakishuto/Translation-Gummy/blob/master/image/demo.gummy-journal.gif?raw=true)

