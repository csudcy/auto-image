<html>
  <head>
    <title>Auto Image Testing</title>
  </head>
  <body>
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
                <td>{{ scores[scorer] }}</td>
              {% endfor %}
          </tr>
        {% endfor %}
    </tbody>
    </table>
  </body>
</html>
