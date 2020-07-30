<!--
  This is a template for templates.
  You have to use the following argments:
  - "title"      : Article Title.
  - "contents"   : Article Contents.
    - "headline" : Headline for one block.
    - "en"       : English text.
    - "ja"       : Translated Japanese text.
-->
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="twitter:card" content="summary" />
    <meta name="twitter:site" content="@cabernet_rock" />
    <meta property="og:url" content="https://github.com/iwasakishuto/Translation-Gummy" />
    <meta property="og:title" content="Translation-Gummy" />
    <meta property="og:description" content="Translation Gummy is a magical gadget which enables user to be able to speak and understand other languages." />
    <meta property="og:image" content="https://github.com/iwasakishuto/Translation-Gummy/blob/master/image/header.png?raw=true" />
    <meta name="slack-app-id" content="A017FQB5GV9">
    <title>{{ title }}</title>
  </head>
  <body>
    {% for content in contents %}
    {% endfor %}
    <style>
    </style>
  </body>
</html>