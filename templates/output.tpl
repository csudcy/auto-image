<html>
  <head>
    <title>Auto Image Testing</title>
  </head>
  <body>
    <h1>Scorer Stats</h1>
    <table border="1">
      <thead>
        <tr>
          <th>Scorer</th>
          <th>Min</th>
          <th>Mean</th>
          <th>Median</th>
          <th>Max</th>
        </tr>
      </thead>
      <tbody>
        {% for scorer in scorers %}
          <tr>
              <th>{{ scorer }}</th>
              <td>{{ '{:.03f}'.format(stats[scorer].min) }}</td>
              <td>{{ '{:.03f}'.format(stats[scorer].mean) }}</td>
              <td>{{ '{:.03f}'.format(stats[scorer].median) }}</td>
              <td>{{ '{:.03f}'.format(stats[scorer].max) }}</td>
          </tr>
        {% endfor %}
      </tbody>
    </table>

    <h1>Counts</h1>
    {{ total_counter }}
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
          <th>Classifications</th>
          {% for scorer in scorers %}
            <th>{{ scorer }}</th>
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
              <td>{{ scores['_total'] }}</td>
              <td>{{ scores['_classifications'] }}</td>
              {% for scorer in scorers %}
                {% if scorer in scores %}
                  <td>{{ '{:.03f}'.format(scores[scorer]) }}</td>
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
