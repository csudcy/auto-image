{% extends 'base.tpl' %}

{% block title %}Page {{ page_index + 1 }} of {{ total_pages }}{% endblock %}

{% block content %}
  <div class="nav">
    <form action="/grid" method="get">
      <span class="pagination">
        {% if page_index > 0 %}
          <button class="icon" type="submit" name="page_index" value="0">⏪</button>
          <button class="icon" type="submit" name="page_index" value="{{ page_index - 1}}">⬅️</button>
        {% else %}
          <span class="icon">⏪</span>
          <span class="icon">⬅️</span>
        {% endif %}
        {{ page_index + 1 }}
        {% if page_index < total_pages - 1 %}
          <button class="icon" type="submit" name="page_index" value="{{ page_index + 1}}">➡️</button>
          <button class="icon" type="submit" name="page_index" value="{{ total_pages - 1}}">⏩</button>
        {% else %}
          <span class="icon">➡️</span>
          <span class="icon">⏩</span>
        {% endif %}
      </span>

      <span class="settings">
        <input type="number" min="10" max="1000" name="page_size" value="{{ page_size }}"/>
        <input type="checkbox" name="chosen_only" id="chosen_only" {% if chosen_only %}checked{% endif %}/>
        <label for="chosen_only">Chosen only</label>
        <button type="submit">Go</button>
      </span>
    </form>
  </div>

  {% for result in page %}
    <span class="grid">
      <a target="_blank" href="/result/{{ result.file_id }}">
        <div class="image-thumbnail" title="{{ result.file_id }}">
          <img src="/image/{{ result.file_id }}"/>
        </div>
      </a>
    </span>
  {% endfor %}
{% endblock %}
