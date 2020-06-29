# coding: utf-8
import os
from jinja2 import Environment, FileSystemLoader
from kerasy.utils import toBLUE

from .utils import TEMPLATES_DIR
ARTICLE_FMT = """<h2>{headline}</h2>
<table>
  <thead>
    <tr>
      <th class="en">English</th>
      <th class="ja">日本語</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td class="en">{en}</td>
      <td class="ja">{ja}</td>
    </tr>
  </tbody>
</table>
"""

def make_content(headline="", en="", ja=""):
    return ARTICLE_FMT.format(headline=headline, en=en, ja=ja)

def render_paper(path, template="paper.tpl", title="", content=""):
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template(template)
    
    data = {"title" : title, "content" : content}    
    with open(path, mode="w") as f:
        f.write(template.render(data))
    print(f"Save file at {toBLUE(path)}")