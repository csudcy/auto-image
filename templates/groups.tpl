<html>
  <head>
    <title>Auto Image - Groups</title>
  </head>
  <body>
    <h1>Groups</h1>
    <table border="1">
      <thead>
        <tr>
          <th>Group</th>
          <th>Count</th>
          <th colspan="99">Images</th>
        </tr>
      </thead>
      <tbody>
        {% for group in groups %}
          <tr>
              <th>{{ loop.index }}</th>
              <td>{{ group | length }}</td>
              {% for result in group %}
                <td {% if result.is_chosen %}style="background-color: lightblue;"{% endif %}>
                  {{ result.file_id }}<br/>
                  {{ '{:.03f}'.format(result.total) }}<br/>
                  {{ result.is_chosen and 'Yes' or '-' }}<br/>
                  <a href="{{ result.file_id }}" target="_blank">
                    <img src="{{ result.file_id }}" style="max-height: 100px;">
                  </a>
                </td>
              {% endfor %}
          </tr>
        {% endfor %}
      </tbody>
    </table>
  </body>
</html>
