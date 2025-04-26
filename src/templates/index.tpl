{% extends 'base.tpl' %}

{% block title %}Home{% endblock %}

{% block extra_head %}
  <link rel="stylesheet" href="/static/index.css">
{% endblock %}

{% block content %}
  <h1>Welcome!</h1>
  <div class="overview">
    <div>
      {{ "{:,}".format(count_total) }}
      <div>Images</div>
    </div>
    <div>
      {{ "{:,}".format(count_chosen) }}
      <div>Chosen</div>
    </div>
  </div>
{% endblock %}
