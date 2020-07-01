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

You need to **set these environment variables in `.env` file**, or call function with keyword argument (`{alias : value}`). See [`gummy/utils/environ_utils.py`](https://github.com/iwasakishuto/Translation-Gummy/blob/master/gummy/utils/environ_utils.py) for details.

**There is an import rule.**

- keywargs in function is `hoge`
- alias is `prefix` (unique to function) + `hoge`
- Environment Variable` is `TRANSLATION_GUMMY_` + `prefix.upper()` + `hoge.upper()`

| alias | Variable | Example |
|:-:|:-:|:-|
| `gateway_url`     | `TRANSLATION_GUMMY_GATEWAY_URL`        | https://gateway.itc.u-tokyo.ac.jp/dana-na/auth/|url_default/welcome.cgi |
| `gateway_username`   | `TRANSLATION_GUMMY_GATEWAY_USERNAME`   | admin |
| `gateway_password`   | `TRANSLATION_GUMMY_GATEWAY_PASSWORD`   | 123456 |
| `gateway_submit_id`  | `TRANSLATION_GUMMY_GATEWAY_SUBMIT_ID`  | submit |
| `gateway_confirm_id` | `TRANSLATION_GUMMY_GATEWAY_CONFIRM_ID` | confirm |
| `gateway_url_format` | `TRANSLATION_GUMMY_GATEWAY_URL_FORMAT` | https://gateway.itc.u-tokyo.ac.jp/,DanaInfo={url},SSL |

## How to use?

- **Translate from English to Japanese.**
    ```sh
    # @ ~/Github/Translation-Gummy
    $ python gummy/deepl.py -q "This is a pen."
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
    from gummy.render import make_content
    from gummy.render import render_paper

    content = make_content(headline="Abstruct", en="English", ja="日本語")
    render_paper("hoge.html", title="Title", content=content)
    >>> Save file at hoge.html
    ```
- **Make pdf**
    ```python
    from gummy.main import make_html
    make_html(url = "https://doi.org/10.1038/171737a0")
    ```