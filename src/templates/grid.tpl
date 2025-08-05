{% extends 'base.tpl' %}

{% block title %}Page {{ settings.page_index + 1 }}{% endblock %}

{% block extra_head %}
  <link rel="stylesheet" href="/static/grid.css">
  <script type="text/javascript" src="/static/grid.js"></script>
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
            step="0.1"
        />
        -
        <input
            type="number"
            name="score_to"
            value="{{ settings.score_to }}"
            min="-5"
            max="5"
            step="0.1"
        />

        <span class="heading">Location</span>
        <label for="location_name">Name contains</label><br/>
        <input
            type="text"
            name="location_name"
            id="location_name"
            {% if settings.location_name %}
              value="{{ settings.location_name }}"
            {% endif %}
        /><br/>
        <span class="bounds">
          <label for="north">N</label>
          <input
              type="text"
              name="north"
              id="north"
              {% if settings.north != None %}
                value="{{ settings.north }}"
              {% endif %}
          /><br/>
          <label for="south">S</label>
          <input
              type="text"
              name="south"
              id="south"
              {% if settings.south != None %}
                value="{{ settings.south }}"
              {% endif %}
          /><br/>
          <label for="east">E</label>
          <input
              type="text"
              name="east"
              id="east"
              {% if settings.east != None %}
                value="{{ settings.east }}"
              {% endif %}
          /><br/>
          <label for="west">W</label>
          <input
              type="text"
              name="west"
              id="west"
              {% if settings.west != None %}
                value="{{ settings.west }}"
              {% endif %}
          />
        </span>

        <span class="heading">OCR Coverage</span>
        <input
            type="number"
            name="ocr_coverage_from"
            {% if settings.ocr_coverage_from != None %}
              value="{{ settings.ocr_coverage_from }}"
            {% endif %}
            min="0"
            max="1"
            step="0.01"
        />
        -
        <input
            type="number"
            name="ocr_coverage_to"
            {% if settings.ocr_coverage_to != None %}
              value="{{ settings.ocr_coverage_to }}"
            {% endif %}
            min="0"
            max="1"
            step="0.01"
        />

        <span class="heading">OCR text contains</span>
        <input
            type="text"
            name="ocr_text"
            {% if settings.ocr_text %}
              value="{{ settings.ocr_text }}"
            {% endif %}
        />

        <span class="heading">Page Size</span>
        <input
            type="number"
            name="page_size"
            value="{{ settings.page_size }}"
            min="1"
            max="100"
        />

        <span class="heading">Sort</span>
        <select name="sort_type">
          <option
              value="taken"
              {% if settings.sort_type.value == 'taken' %}selected{% endif %}
          >
            Taken
          </option>
          <option
              value="total"
              {% if settings.sort_type.value == 'total' %}selected{% endif %}
          >
            Score
          </option>
          <option
              value="ocr_coverage"
              {% if settings.sort_type.value == 'ocr_coverage' %}selected{% endif %}
          >
            OCR Coverage
          </option>
        </select>
        <input
            type="checkbox"
            name="sort_reverse"
            id="sort_reverse"
            {% if settings.sort_reverse %}checked{% endif %}
        />
        <label for="sort_reverse">Reverse</label><br/>

        <button type="submit">Apply</button>
      </span>
    </form>
    <form action="/grid" method="get">
      <input type="hidden" name="page_size" value="{{ settings.page_size }}"/>
      <button type="submit">Clear</button>
    </form>
  </div>

  <div class="content-panel">
    {%- for result in page -%}
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
          {% if result.group_index %}
            <span class="group-text">{{ result.group_index }}</span>
          {% endif %}
        </a>
      </span>
    {%- endfor -%}
  </div>
{% endblock %}
