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
    <title>{{ title }}</title>
  </head>
  <body>
    <h1> {{ title }} </h1>
    {% for content in contents %}
<<<<<<< Updated upstream
    <h2>{{ content.headline }}</h2>
    <table>
      <thead>
        <tr>
          <th class="en">English</th>
          <th class="ja" lang="ja">日本語</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="en">{{ content.en }}</td>
          <td class="ja" lang="ja">{{ content.ja }}</td>
        </tr>
      </tbody>
    </table>
=======
      {% if 'headline' in content %}
        <h2>{{ content.headline }}</h2>
      {% endif %}
      {% if 'en' in content %}
        <table>
          <!-- <thead>
            <tr>
              <th class="en">English</th>
              <th class="ja" lang="ja">日本語</th>
            </tr>
          </thead> -->
          <tbody>
            <tr>
              <td class="en">{{ content.en }}</td>
              <td class="ja" lang="ja">{{ content.ja }}</td>
            </tr>
          </tbody>
        </table>
      {% endif %}
      {% if 'img' in content %}
        <p class="img_center">
          {{ content.img }}
        </p>
      {% endif %}
>>>>>>> Stashed changes
    {% endfor %}
    <style>
      body {
        font-family: Times New Roman;
        margin: 0;
      }
      h1 {
        text-align: center;
        font-size: 2.5em;
      }
      h2 {
        border-bottom: 2px solid #d5d5d5;
      }
      table {
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
      }
      thead {
        font-size: 1.15em;
        font-weight: bold;
      }
      td, th {
        width: 50%;
        vertical-align: top;
      }
      .ja {
        font-size: 0.85em;
      }
      p.img_center{
        text-align: center;
      }
    </style>
  </body>
</html>