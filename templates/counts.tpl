<html>
  <head>
    <title>Counts - Auto Image</title>
  </head>
  <body>
    <h1>Counts</h1>
    <table border="1">
      <thead>
        <tr>
          <th rowspan="2">Score</th>
          <th colspan="2">Overall</th>
          <th colspan="2">Recent</th>
          <th colspan="2">Old</th>
        </tr>
        <tr>
          <th>Count</th>
          <th>Chosen</th>
          <th>Count</th>
          <th>Chosen</th>
          <th>Count</th>
          <th>Chosen</th>
        </tr>
      </thead>
      <tbody>
        {% for score, stats in score_counts.items() | sort(reverse=True) %}
          <tr>
              <th {% if score < minimum_score %}style="background-color: lightpink;"{% endif %}>
                {{ score }}
              </th>
              <td>{{ stats.overall_total }}</td>
              <td>{{ stats.overall_chosen }}</td>
              <td>{{ stats.recent_total or '-' }}</td>
              <td>{{ stats.recent_chosen or '-' }}</td>
              <td>{{ stats.old_total or '-' }}</td>
              <td>{{ stats.old_chosen or '-' }}</td>
          </tr>
        {% endfor %}
        <tr>
            <th>Total</th>
            <td>{{ total_counts.overall_total }}</td>
            <td>{{ total_counts.overall_chosen }}</td>
            <td>{{ total_counts.recent_total or '-' }}</td>
            <td>{{ total_counts.recent_chosen or '-' }}</td>
            <td>{{ total_counts.old_total or '-' }}</td>
            <td>{{ total_counts.old_chosen or '-' }}</td>
        </tr>
      </tbody>
    </table>
  </body>
</html>
