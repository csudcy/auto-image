<html>
  <head>
    <title>Scores - Auto Image</title>
  </head>
  <body>
    <h1>Scores</h1>
    <table border="1">
      <thead>
        <tr>
          <th>File</th>
          <th>Image</th>
          <th>Total</th>
          <th>Chosen?</th>
          <th>Recent?</th>
          {% for label in label_weights.keys() %}
            <th>{{ label }}</th>
          {% endfor %}
        </tr>
        <tr>
          <th colspan="5">Weight (Total: {{ total_weight }})</th>
          {% for weight in label_weights.values() %}
            <td>{{ weight }}</td>
          {% endfor %}
        </tr>
        <tr>
          <th colspan="5">Min</th>
          {% for label in label_weights.keys() %}
            <td>{{ '{:.03f}'.format(stats[label].min) }}</td>
          {% endfor %}
        </tr>
        <tr>
          <th colspan="5">Mean</th>
          {% for label in label_weights.keys() %}
            <td>{{ '{:.03f}'.format(stats[label].mean) }}</td>
          {% endfor %}
        </tr>
        <tr>
          <th colspan="5">Median</th>
          {% for label in label_weights.keys() %}
            <td>{{ '{:.03f}'.format(stats[label].median) }}</td>
          {% endfor %}
        </tr>
        <tr>
          <th colspan="5">Max</th>
          {% for label in label_weights.keys() %}
            <td>{{ '{:.03f}'.format(stats[label].max) }}</td>
          {% endfor %}
        </tr>
      </thead>
      <tbody>
        {% for result in results %}
          <tr>
              <td>
                {{ result.file_id }}
                {% if result.group_index %}
                  <br/>
                  Group: <span style="background-color: lightgreen;">{{ result.group_index }}</span>.
                {% endif %}
              </td>
              <td>
                <a href="{{ result.file_id }}" target="_blank">
                  <img src="{{ result.file_id }}" style="max-height: 100px;">
                </a>
              </td>
              <td {% if result.total < minimum_score %}style="background-color: lightpink;"{% endif %}>
                {{ '{:.03f}'.format(result.total) }}
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
              {% for label in label_weights.keys() %}
                {% if label in result.scores %}
                  <td style="background-color: rgb({{ '{:.01f}'.format((1-result.scores[label]) * 255) }}, {{ '{:.01f}'.format((1-result.scores[label]) * 255) }}, 255)">
                    {{ '{:.03f}'.format(result.scores[label]) }}
                  </td>
                {% else %}
                  <td>-</td>
                {% endif %}
              {% endfor %}
          </tr>
        {% endfor %}
      </tbody>
    </table>
  </body>
</html>
