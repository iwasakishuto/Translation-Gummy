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
    # @ ~/Github/Translation-Gummy
    from gummy.render import make_content
    from gummy.render import render_paper

    content = make_content(headline="Abstruct", en="English", ja="日本語")
    render_paper("hoge.html", title="Title", content=content)
    >>> Save file at hoge.html
    ```
