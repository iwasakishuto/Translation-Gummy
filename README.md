# Translation Gummy

![header](image/header.png)

**Translation Gummy** is a **_magical gadget_** which enables user to be able to speak and understand other languages.

## Installation

There are two ways to install **`Translation-Gummy`**:

- **Install PyGuitar from PyPI (recommended):**
    ```
    $ sudo pip install Translation-Gummy
    ```
- **Alternatively: install PyGuitar from the GitHub source:**
    ```
    $ git clone https://github.com/iwasakishuto/Translation-Gummy.git
    $ cd Translation-Gummy
    $ sudo python setup.py install
    ```

## Environment Variable

When you use `gateways`, you need to **set environment variables in `.env` file**, or call a function with keyword argument.

```python
from gummy import gateways
from gummy.utils import get_driver
gateway = gateways.get("utokyo")
>>> TRANSLATION_GUMMY_UTOKYO_GATEWAY_USERNAME is not set.
>>> TRANSLATION_GUMMY_UTOKYO_GATEWAY_PASSWORD is not set.
>>> EnvVariableNotDefinedWarning: Please set environment variable in /Users/iwasakishuto/.gummy/.env
```

1. **Set environment variables in `.env` file.**
    ```python
    from gummy.utils import where_is_envfile, show_environ, write_environ, read_environ
    default_dotenv_path = where_is_envfile()
    print(f"default dotenv path: '{default_dotenv_path}'")
    >>> default dotenv path: '/Users/iwasakishuto/.gummy/.env'
    # Write and update `.env` file.
    write_environ(
        TRANSLATION_GUMMY_UTOKYO_GATEWAY_USERNAME="username",
        TRANSLATION_GUMMY_UTOKYO_GATEWAY_PASSWORD="password",
    )
    show_environ(default_dotenv_path)
    >>> TRANSLATION_GUMMY_UTOKYO_GATEWAY_USERNAM = "username"
    >>> TRANSLATION_GUMMY_UTOKYO_GATEWAY_PASSWOR = "password"
    # Call with no kwargs.
    gateway = gateways.get("utokyo")
    with get_drive() as driver:
        driver = gateway.passthrough(driver)
        :
    ```
2. **Call a function with keyword argument.**
    ```python
    # Call with kwargs.
    with get_drive() as driver:
        driver = gateway.passthrough(driver, username="username", password="password")
        :
    ```

#### Naming conventions

```python
ENV_VARNAMES = "{1}_{2}_GATEWAY_{3}"
# 1 = TRANSLATION_GUMMY_ENVNAME_PREFIX (`gummy.utils.environ_utils.py`)
# 2 = Uppercase of class name without 'GateWay'
# 3 = varnames, which is also the key of `keywargs`
```

<details>
    <summary>Example</summary>  

```python
# gummy.utils.environ_utils.py
TRANSLATION_GUMMY_ENVNAME_PREFIX = "TRANSLATION_GUMMY"

# gummy.gateways.py
class GummyAbstGateWay(metaclass=ABCMeta):
    def __init__(self, url=None, verbose=1, env_varnames=[], dotenv_path=DOTENV_PATH):
        self.env_varnames = [f"{TRANSLATION_GUMMY_ENVNAME_PREFIX}_{self.__class__.__name__.replace('GateWay', '').upper()}_GATEWAY_{v.upper()}" for v in env_varnames]

class Hoge(GummyAbstGateWay):
    def __init__():
        super().__init__(env_varnames=["username"])

hoge = Hoge()
hoge.envvarnames = ["{1}_{2}_GATEWAY_{3}"]
# 1 = TRANSLATION_GUMMY_ENVNAME_PREFIX = "TRANSLATION_GUMMY"
# 2 = HOGE (= Hoge.upper())
# 3 = USERNAME (= username.upper())
```

</details>

## How to use?

- **Translate from English to Japanese.**
    ```python
    from gummy import TranslationGummy
    model = TranslationGummy(translator="deepl")
    model.en2ja(query="This is a pen.")
    ```
    <details>
      <summary>Output</summary>  
  
      [success] local driver can be built.
      [failure] remote driver can't be built.
      DRIVER_TYPE: local
      query: https://www.deepl.com/en/translator#en/ja/This%20is%20a%20pen.
      DeepL 01/10[##------------------] 10.00% - 1.068[s]   japanese: これはペンです。
      japanese:
      これはペンです。

    </details>
- **Render templates.**
    ```python
    from gummy import TranslationGummy
    model = TranslationGummy(gateway="utokyo", translator="deepl")
    model.toHTML(url, path)
    ```
- **Make pdf**
    ```python
    from gummy import TranslationGummy
    model = TranslationGummy(gateway="utokyo", translator="deepl")
    model.toPDF(url, path)
    ```