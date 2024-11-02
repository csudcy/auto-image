<html>
  <head>
    <title>Auto Image Testing</title>
  </head>
  <body>
    <h1>Counts</h1>
    <table border="1">
      <thead>
        <tr>
          <th>Score</th>
          <th>Count</th>
        </tr>
      </thead>
      <tbody>
        {% for score, count in total_counter.items() | sort(reverse=True) %}
          <tr>
              <td>{{ score }}</td>
              <td>{{ count }}</td>
          </tr>
        {% endfor %}
      </tbody>
    </table>

    <h1>Scores</h1>
    <table border="1">
      <thead>
        <tr>
          <th>File</th>
          <th>Image</th>
          <th>Total</th>
          {% for label in label_weights.keys() %}
            <th>{{ label }}</th>
          {% endfor %}
        </tr>
        <tr>
          <th colspan="3">Weight</th>
          {% for weight in label_weights.values() %}
            <td>{{ weight }}</td>
          {% endfor %}
        </tr>
        <tr>
          <th colspan="3">Min</th>
          {% for label in label_weights.keys() %}
            <td>{{ '{:.03f}'.format(stats[label].min) }}</td>
          {% endfor %}
        </tr>
        <tr>
          <th colspan="3">Mean</th>
          {% for label in label_weights.keys() %}
            <td>{{ '{:.03f}'.format(stats[label].mean) }}</td>
          {% endfor %}
        </tr>
        <tr>
          <th colspan="3">Median</th>
          {% for label in label_weights.keys() %}
            <td>{{ '{:.03f}'.format(stats[label].median) }}</td>
          {% endfor %}
        </tr>
        <tr>
          <th colspan="3">Max</th>
          {% for label in label_weights.keys() %}
            <td>{{ '{:.03f}'.format(stats[label].max) }}</td>
          {% endfor %}
        </tr>
      </thead>
      <tbody>
        {% for file_id, scores in results %}
          <tr>
              <td>{{ file_id }}</td>
              <td>
                <a href="{{ path_prefix }}/{{ file_id }}" target="_blank">
                  <img src="{{ path_prefix }}/{{ file_id }}" style="max-height: 100px;">
                </a>
              </td>
              <td>{{ '{:.03f}'.format(scores['_total']) }}</td>
              {% for label in label_weights.keys() %}
                {% if label in scores %}
                  <td style="background-color: rgb({{ '{:.01f}'.format((1-scores[label]) * 255) }}, {{ '{:.01f}'.format((1-scores[label]) * 255) }}, 255)">
                    {{ '{:.03f}'.format(scores[label]) }}
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
