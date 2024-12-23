<html>
  <head>
    <title>OCR {{ index_min }}-{{ index_max }} - Auto Image</title>
  </head>
  <body>
    <h1>OCR {{ index_min }}-{{ index_max }}</h1>
    <table border="1">
      <thead>
        <tr>
          <th>Index</th>
          <th>File</th>
          <th>Image</th>
          <th>Chosen?</th>
          <th>Recent?</th>

          <th>Length</th>
          <th>Coverage</th>
          <th>Text</th>
        </tr>
      </thead>
      <tbody>
        {% for result in results %}
          <tr>
              <td>{{ loop.index0 + index_min }}</td>
              <td>
                {{ result.file_id }}
                {% if result.group_index %}
                  <br/>
                  Group: <span style="background-color: lightgreen;">{{ result.group_index }}</span>.
                {% endif %}
              </td>
              <td>
                <a href="{{ result.path }}" target="_blank">
                  <img src="{{ result.path }}" style="max-height: 100px;">
                </a>
              </td>
              {% if result.is_chosen %}
                <td style="background-color: lightblue;">Yes</td>
              {% else %}
                <td>-</td>
              {% endif %}
              {% if result.is_recent %}
                <td style="background-color: lightblue;">Yes</td>
              {% else %}
                <td>-</td>
              {% endif %}

              <td {% if result.ocr_text|length >= ocr_text_threshold %}style="background-color: lightpink;"{% endif %}>
                {{ result.ocr_text|length }}
              </td>
              <td {% if result.ocr_coverage >= ocr_coverage_threshold %}style="background-color: lightpink;"{% endif %}>
                {{ '{:.03f}'.format(result.ocr_coverage) }}
              </td>
              <td>
                {{ result.ocr_text }}
              </td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
  </body>
</html>
