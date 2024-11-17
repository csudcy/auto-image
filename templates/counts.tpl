<html>
  <head>
    <title>Counts - Auto Image</title>
  </head>
  <body>
    <h1>Counts</h1>
    <table border="1">
      <thead>
        <tr>
          <th>Score</th>
          <th>Count</th>
          <th>Recent</th>
          <th>Chosen</th>
        </tr>
      </thead>
      <tbody>
        {% for score, stats in score_stats.items() | sort(reverse=True) %}
          <tr>
              <th {% if score < minimum_score %}style="background-color: lightpink;"{% endif %}>
                {{ score }}
              </th>
              <td>{{ stats.count }}</td>
              <td>{{ stats.recent_count or '-' }}</td>
              <td>{{ stats.chosen_count or '-' }}</td>
          </tr>
        {% endfor %}
        <tr>
            <th>Total</th>
            <td>{{ total_stats.count }}</td>
            <td>{{ total_stats.recent_count or '-' }}</td>
            <td>{{ total_stats.chosen_count or '-' }}</td>
        </tr>
      </tbody>
    </table>
  </body>
</html>
