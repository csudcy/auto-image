{% extends 'base.tpl' %}

{% block title %}{{ result.file_id }}{% endblock %}

{% block content %}
  <h1>{{ result.file_id }}</h1>
  <span class="grid {% if result.is_chosen %}chosen{% endif %} {% if result.include_override == False %}exclude{% endif %}">
    <a target="_blank" href="/image/{{ result.file_id }}">
      <div class="image-thumbnail large" title="{{ result.file_id }}">
        <img src="/image/{{ result.file_id }}"/>
      </div>
    </a>
  </span>
  <table>
    <tr>
      <th>Chosen?</th>
      <td>{{ result.is_chosen }}</td>
    </tr>
    <tr>
      <th>Override?</th>
      <td>
        {% if result.include_override == True %}
          Include
        {% else %}
          {% if result.include_override == False %}
            Exclude
          {% else %}
            -
          {% endif %}
        {% endif %}
      </td>
    </tr>
    <tr>
      <th>Group Index</th>
      <td>
        {% if result.group_index %}
          <a target="_blank" href="/group/{{ result.group_index }}">
            {{ result.group_index }}
          </a>
        {% else %}
          -
        {% endif %}
      </td>
    </tr>

    <tr>
      <th>Location</th>
      <td>
        {% if result.location %}
          <a
              href="http://www.openstreetmap.org/?mlat={{ result.lat_lon.lat }}&mlon={{ result.lat_lon.lon }}&zoom=9"
              target="_blank">
              {{ result.location }}
            </a>
        {% else %}
          -
        {% endif %}
      </td>
    </tr>
    <tr>
      <th>Taken</th>
      <td>{{ result.taken }}</td>
    </tr>
    <tr>
      <th>Total Score</th>
      <td>{{ result.total }}</td>
    </tr>

    <tr>
      <th>Ocr Coverage</th>
      <td>{{ result.ocr_coverage or '-' }}</td>
    </tr>
    <tr>
      <th>Ocr Text</th>
      <td>{{ result.ocr_text }}</td>
    </tr>
  </table>
{% endblock %}
