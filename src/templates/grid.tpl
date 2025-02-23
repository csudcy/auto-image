{% extends 'base.tpl' %}

{% block title %}Page {{ settings.page_index + 1 }}{% endblock %}

{% block extra_head %}
  <link rel="stylesheet" href="/static/grid.css">
{% endblock %}

{% block content %}
  <div class="nav-panel">
    <form action="/grid" method="get">
      {# Add a hidden submit button here so pressing enter on any of the filter fields moves to first page #}
      <button type="submit" name="page_index" value="0" style="display: none;">-</button>

      <span class="pagination">
        {% if settings.page_index > 0 %}
          <button class="icon" type="submit" name="page_index" value="0">⏪</button>
          <button class="icon" type="submit" name="page_index" value="{{ settings.page_index - 1}}">⬅️</button>
        {% else %}
          <span class="icon">⏪</span>
          <span class="icon">⬅️</span>
        {% endif %}
        {{ settings.page_index + 1 }} / {{ total_pages }}
        {% if settings.page_index < total_pages - 1 %}
          <button class="icon" type="submit" name="page_index" value="{{ settings.page_index + 1}}">➡️</button>
          <button class="icon" type="submit" name="page_index" value="{{ total_pages - 1}}">⏩</button>
        {% else %}
          <span class="icon">➡️</span>
          <span class="icon">⏩</span>
        {% endif %}
      </span>

      <span class="heading">
        Matched {{ filtered_results }} of {{ total_results }}
      </span>

      <span class="settings">
        <span class="heading">Chosen</span>
        <input
            type="checkbox"
            name="chosen_yes"
            id="chosen_yes"
            {% if settings.chosen_yes %}checked{% endif %}
        />
        <label for="chosen_yes">Yes</label><br/>
        <input
            type="checkbox"
            name="chosen_no"
            id="chosen_no"
            {% if settings.chosen_no %}checked{% endif %}
        />
        <label for="chosen_no">No</label><br/>

        <span class="heading">Override</span>
        <input
            type="checkbox"
            name="override_include"
            id="override_include"
            {% if settings.override_include %}checked{% endif %}
        />
        <label for="override_include">Include</label><br/>
        <input
            type="checkbox"
            name="override_exclude"
            id="override_exclude"
            {% if settings.override_exclude %}checked{% endif %}
        />
        <label for="override_exclude">Exclude</label><br/>
        <input
            type="checkbox"
            name="override_unset"
            id="override_unset"
            {% if settings.override_unset %}checked{% endif %}
        />
        <label for="override_unset">Unset</label><br/>

        <span class="heading">Date</span>
        <input
            type="date"
            name="date_from"
            value="{{ settings.date_from }}"
            min="{{ date_min }}"
            max="{{ date_max }}"
        />
        <input
            type="date"
            name="date_to"
            value="{{ settings.date_to }}"
            min="{{ date_min }}"
            max="{{ date_max }}"
        />

        <span class="heading">Score</span>
        <input
            type="number"
            name="score_from"
            value="{{ settings.score_from }}"
            min="-5"
            max="5"
        />
        -
        <input
            type="number"
            name="score_to"
            value="{{ settings.score_to }}"
            min="-5"
            max="5"
        />

        <span class="heading">Location contains</span>
        <input
            type="text"
            name="location_name"
            value="{{ settings.location_name }}"
        />

        <span class="heading">OCR Coverage</span>
        <input
            type="number"
            name="ocr_coverage_from"
            value="{{ settings.ocr_coverage_from }}"
            min="0"
            max="100"
        />
        -
        <input
            type="number"
            name="ocr_coverage_to"
            value="{{ settings.ocr_coverage_to }}"
            min="0"
            max="100"
        />

        <span class="heading">OCR text contains</span>
        <input
            type="text"
            name="ocr_text"
            value="{{ settings.ocr_text }}"
        />

        <span class="heading">Page Size</span>
        <input
            type="number"
            name="page_size"
            value="{{ settings.page_size }}"
            min="10"
            max="1000"
        />

        <button type="submit">Apply</button>
      </span>
    </form>
  </div>

  <div class="content-panel">
    {% for result in page %}
      <span class="grid {% if result.is_chosen %}chosen{% endif %} {% if result.include_override == False %}exclude{% endif %}">
        <a target="_blank"
          {% if result.group_index %}
            href="/group/{{ result.group_index }}"
          {% else %}
            href="/result/{{ result.file_id }}"
          {% endif %}
          >
          <div class="image-thumbnail" title="{{ result.file_id }}">
            <img src="/image/{{ result.file_id }}"/>
          </div>
        </a>
      </span>
    {% endfor %}
  </div>
{% endblock %}
