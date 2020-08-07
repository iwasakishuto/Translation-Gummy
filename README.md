# Translation Gummy

![header](https://github.com/iwasakishuto/Translation-Gummy/blob/master/image/header.png?raw=true)
[![PyPI version](https://badge.fury.io/py/Translation-Gummy.svg)](https://pypi.org/project/Translation-Gummy/)
[![GitHub version](https://badge.fury.io/gh/iwasakishuto%2FTranslation-Gummy.svg)](https://github.com/iwasakishuto/Translation-Gummy)
![Python package](https://github.com/iwasakishuto/Translation-Gummy/workflows/Python%20package/badge.svg)
![Upload Python Package](https://github.com/iwasakishuto/Translation-Gummy/workflows/Upload%20Python%20Package/badge.svg)
[![license](https://img.shields.io/github/license/mashape/apistatus.svg?maxAge=2592000)](https://github.com/iwasakishuto/Kerasy/blob/gh-pages/LICENSE)
[![website](https://img.shields.io/badge/website-Translation--Gummy-lightblue)](https://elb.translation-gummy.com/)
[![Add to Slack](https://platform.slack-edge.com/img/add_to_slack.png)](https://elb.translation-gummy.com/slack_auth_begin)

**Translation Gummy** is a **_magical gadget_** which enables user to be able to speak and understand other languages. **※ Supported journals are listed [here](https://github.com/iwasakishuto/Translation-Gummy/wiki/Supported-journals).**

## Installation

1. Install **`Translation-Gummy`** (There are two ways to install):
    - **Install from PyPI (recommended):**
        ```sh
        $ sudo pip install Translation-Gummy
        ```
   - **Alternatively: install PyGuitar from the GitHub source:**
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
      <img src="image/demo.gummy-translate.gif" alt="gummy-translate">
    </details>
- **Create PDF (with translation)**
    - **Python Module:**
    ```python
    >>> from gummy import TranslationGummy
    >>> gummy = TranslationGummy(gateway="utokyo", translator="deepl")
    >>> pdfpath = gummy.toPDF(url="https://doi.org/10.1038/171737a0", delete_html=True)
    ```
    - **Command line:**
    ```sh
    $ gummy-journal "https://doi.org/10.1038/171737a0"
    ```
    <details>
      <summary><b>Output</b></summary>  
      <img src="image/demo.gummy-journal.gif" alt="gummy-journal">
    </details>

## Environment Variable

When you use `gateways`, you need to **set environment variables in `.env` file**, or call a function with keyword argument.

```python
>>> from gummy import gateways
>>> from gummy.utils import get_driver
>>> gateway = gateways.get("utokyo")
TRANSLATION_GUMMY_UTOKYO_GATEWAY_USERNAME is not set.
TRANSLATION_GUMMY_UTOKYO_GATEWAY_PASSWORD is not set.
EnvVariableNotDefinedWarning: Please set environment variable in /Users/iwasakishuto/.gummy/.env
```

1. **Set environment variables in `.env` file.**
    ```python
    >>> from gummy.utils import where_is_envfile, show_environ, write_environ, read_environ
    >>> default_dotenv_path = where_is_envfile()
    >>> print(f"default dotenv path: '{default_dotenv_path}'")
    default dotenv path: '/Users/iwasakishuto/.gummy/.env'

    # Write and update `.env` file.
    >>> write_environ(
    ...    TRANSLATION_GUMMY_UTOKYO_GATEWAY_USERNAME="username",
    ...    TRANSLATION_GUMMY_UTOKYO_GATEWAY_PASSWORD="password",
    >>> )
    >>> show_environ(default_dotenv_path)
    TRANSLATION_GUMMY_UTOKYO_GATEWAY_USERNAM = "username"
    TRANSLATION_GUMMY_UTOKYO_GATEWAY_PASSWOR = "password"

    # Call with no kwargs.
    >>> gateway = gateways.get("utokyo")
    >>> with get_drive() as driver:
    ...    driver = gateway.passthrough(driver)
    ...    :
    ```
2. **Call a function with keyword argument.**
    ```python
    # Call with kwargs.
    >>> with get_drive() as driver:
    ...    driver = gateway.passthrough(driver, username="username", password="password")
    ...    :
    ```

#### Naming conventions

```python
>>> ENV_VARNAMES = "{1}_{2}_GATEWAY_{3}"
# 1 = TRANSLATION_GUMMY_ENVNAME_PREFIX (Define @gummy.utils.environ_utils.py)
# 2 = Uppercase of class name without 'GateWay'
# 3 = varnames, which is also the key of `keywargs`
```

<details>
    <summary>Example</summary>  

```python
# ==============================================================================
# @gummy.utils.environ_utils.py
TRANSLATION_GUMMY_ENVNAME_PREFIX = "TRANSLATION_GUMMY"
# @gummy.gateways.py
class GummyAbstGateWay(metaclass=ABCMeta):
   def __init__(self, url=None, verbose=1, env_varnames=[], dotenv_path=DOTENV_PATH):
        self.env_varnames = [
            TRANSLATION_GUMMY_ENVNAME_PREFIX + "_" + \
            self.__class__.__name__.replace('GateWay', '').upper() + "_" + \
            "GATEWAY_" + \
            v.upper() for v in env_varnames
        ]
# ==============================================================================
>>> from gummy.gateways import GummyAbstGateWay
>>> class Hoge(GummyAbstGateWay):
...     def __init__():
...         super().__init__(env_varnames=["username"])

>>> hoge = Hoge()
>>> hoge.envvarnames = ["{1}_{2}_GATEWAY_{3}"]
# 1 = TRANSLATION_GUMMY_ENVNAME_PREFIX = "TRANSLATION_GUMMY"
# 2 = HOGE (= Hoge.upper())
# 3 = USERNAME (= username.upper())
```

</details>