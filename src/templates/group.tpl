{% extends 'base.tpl' %}

{% block title %}Group {{ group_index }}{% endblock %}

{% block content %}
  <h1>Group {{ group_index }}</h1>
  {% for result in results %}
    <span class="grid {% if result.is_chosen %}chosen{% endif %} {% if result.exclude %}exclude{% endif %}">
      <a target="_blank" href="/result/{{ result.file_id }}">
        <div class="image-thumbnail large" title="{{ result.file_id }}">
          <img src="/image/{{ result.file_id }}"/>
        </div>
      </a>
    </span>
  {% endfor %}
{% endblock %}
