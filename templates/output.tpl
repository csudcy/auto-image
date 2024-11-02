<html>
  <head>
    <title>Auto Image Testing</title>
  </head>
  <body>
    <h1>Stats</h1>
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

    <h1>Scores</h1>
    <table border="1">
      <thead>
        <tr>
          <th>File</th>
          <th>Image</th>
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
                <a href="{{ path_prefix }}/{{ file_id }}">
                  <img src="{{ path_prefix }}/{{ file_id }}" style="max-height: 100px;">
                </a>
              </td>
              {% for scorer in scorers %}
                <td>{{ '{:.03f}'.format(scores[scorer]) }}</td>
              {% endfor %}
          </tr>
        {% endfor %}
      </tbody>
    </table>
  </body>
</html>
