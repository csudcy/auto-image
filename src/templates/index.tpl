{% extends 'base.tpl' %}

{% block title %}Home{% endblock %}

{% macro stat_row(title, stats) %}
  <tr>
    <th>{{ title }}</th>
    <td class="number">{{ stats.total }}</td>
    <td class="number">{{ (100 * stats.total / total_counts.total) | round(1) }}%</td>
    <td class="number">{{ stats.chosen }}</td>
    <td class="number">{{ (100 * stats.chosen / total_counts.chosen) | round(1) }}%</td>
  </tr>
{% endmacro %}

{% block content %}
  <h1>Counts</h1>
  <table border="1">
    <thead>
      <tr>
        <th></th>
        <th colspan="2">Count</th>
        <th colspan="2">Chosen</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <th>Total</th>
        <td class="number" colspan="2">{{ total_counts.total }}</td>
        <td class="number">{{ total_counts.chosen }}</td>
        <td class="number">{{ (100 * total_counts.chosen / total_counts.total) | round(1) }}%</td>
      </tr>
      <tr>
        <th colspan="5">
          Groups<br/>
        </th>
      </tr>
      <tr>
        <th>Count</th>
        <td colspan="4" class="number">{{ group_count }}</td>
      </tr>
      <tr>
        <th>Average images</th>
        <td colspan="4" class="number">{{ (grouped_counts.total / group_count) | round(2) }}</td>
      </tr>
      {{ stat_row('Grouped', grouped_counts) }}
      {{ stat_row('Ungrouped', ungrouped_counts) }}
      <tr>
        <th colspan="5">Scores</th>
      </tr>
      {% for score, stats in score_counts.items() | sort(reverse=True) %}
        {{ stat_row(score, stats) }}
      {% endfor %}
    </tbody>
  </table>
  <h1>Processing</h1>
  <table border="1" id="logs-table">
    <thead>
      <tr>
        <th>Timestamp</th>
        <th>Message</th>
      </tr>
    </thead>
    <tbody>
    </tbody>
  </table>
{% endblock %}
