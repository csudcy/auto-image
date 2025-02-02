{% extends 'base.tpl' %}

{% block title %}Page {{ page_index + 1 }} of {{ total_pages }}{% endblock %}

{% block content %}
  {% if page_index > 0 %}
    <a href="?page_index=0">⏪</a>
    <a href="?page_index={{ page_index - 1}}">⬅️</a>
  {% else %}
    ⏪
    ⬅️
  {% endif %}
  {{ page_index + 1 }}
  {% if page_index < total_pages - 1 %}
    <a href="?page_index={{ page_index + 1}}">➡️</a>
    <a href="?page_index={{ total_pages - 1 }}">⏩</a>
  {% else %}
    ➡️
    ⏩
  {% endif %}

  <hr/>

  <ul>
    <li>page_size: {{ page_size }}</li>
  </ul>

  {% for result in page %}
    <a target="_blank" href="/image/{{ result.file_id }}">
      {{ result.file_id }}
      <div class="image-thumbnail">
        <img src="/image/{{ result.file_id }}"/>
      </div>
    </a>
  {% endfor %}
{% endblock %}
