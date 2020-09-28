# Translation Gummy

![header](https://github.com/iwasakishuto/Translation-Gummy/blob/master/image/header.png?raw=true)
[![PyPI version](https://badge.fury.io/py/Translation-Gummy.svg)](https://pypi.org/project/Translation-Gummy/)
[![GitHub version](https://badge.fury.io/gh/iwasakishuto%2FTranslation-Gummy.svg)](https://github.com/iwasakishuto/Translation-Gummy)
![Python package](https://github.com/iwasakishuto/Translation-Gummy/workflows/Python%20package/badge.svg)
![Upload Python Package](https://github.com/iwasakishuto/Translation-Gummy/workflows/Upload%20Python%20Package/badge.svg)
[![license](https://img.shields.io/github/license/mashape/apistatus.svg?maxAge=2592000)](https://github.com/iwasakishuto/Translation-Gummy/blob/master/LICENSE)
[![Documentation](https://img.shields.io/badge/Documentation-portfolio-001d34?style=flat-square)](https://iwasakishuto.github.io/Translation-Gummy/index.html)
[![twitter badge](https://img.shields.io/badge/twitter-Requests-1da1f2?style=flat-square&logo=twitter)](https://www.twitter.com/messages/compose?recipient_id=1042783905697288193&text=Please%20support%20this%20journal%3A%20)
[![Qiita badge1](https://img.shields.io/badge/「ほん訳コンニャク」を食べて論文を読もう-Qiita-64c914?style=flat-square)](https://qiita.com/cabernet_rock/items/670d5cd597bcd9f2ff3f)
[![Qiita badge2](https://img.shields.io/badge/「ほん訳コンニャク」を使ってみよう。-Qiita-64c914?style=flat-square)](https://qiita.com/cabernet_rock/items/1f9bff5e0b9363da312d)
[![website](https://img.shields.io/badge/website-Translation--Gummy-lightblue)](https://elb.translation-gummy.com/)
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
        $ brew install Caskroom/cask/wkhtmltopdf
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

## Quick example

- **[example notebooks](https://nbviewer.jupyter.org/github/iwasakishuto/Translation-Gummy/blob/master/examples/)**
- **Translation**:
    - **Python Module:**
    ```python
    >>> from gummy import TranslationGummy
    >>> gummy = TranslationGummy(translator="deepl")
    DRIVER_TYPE: local
    >>> gummy.en2ja("This is a pen.")
    DeepLTranslator query no.1 01/15 [#-------------------]  6.67% - 1.091[s]
    'これはペンです。'
    ```
    - **Command line:**
    ```sh
    $ gummy-translate "This is a pen."
    [success] local driver can be built.
    [failure] remote driver can't be built.
    DRIVER_TYPE: local
    DeepLTranslator query no.1 01/15 [#-------------------]  6.67% - 1.096[s]
    これはペンです。
    ```
    <details>
      <summary><b>Output</b></summary>  
      <img src="https://github.com/iwasakishuto/Translation-Gummy/blob/master/image/demo.gummy-translate.gif?raw=true" alt="gummy-translate">
    </details>
- **Create PDF (with translation)**
    - **Python Module:**
    ```python
    >>> from gummy import TranslationGummy
    >>> gummy = TranslationGummy(gateway="utokyo", translator="deepl")
    >>> pdfpath = gummy.toPDF(url="https://www.nature.com/articles/ncb0800_500", delete_html=True)
    ```
    - **Command line:**
    ```sh
    $ gummy-journal "https://www.nature.com/articles/ncb0800_500"
    ```
    <details>
      <summary><b>Output</b></summary>  
      <img src="https://github.com/iwasakishuto/Translation-Gummy/blob/master/image/demo.gummy-journal.gif?raw=true" alt="gummy-journal">
    </details>
