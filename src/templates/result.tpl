{% extends 'base.tpl' %}

{% block title %}{{ title }}{% endblock %}

{% block content %}
  <h1>{{ title }}</h1>
  {% if results|length > 1 %}
    <form method="POST">
      <button type="submit" name="include_override" value="false">
        Exclude
      </button>
      <button type="submit" name="include_override" value="none">
        Clear
      </button>
      <button type="submit" name="include_override" value="true">
        Include
      </button>
    </form>
  {% endif %}

  <table>
    {% for result in results %}
      <tr>
        <td>
          <span class="grid {% if result.is_chosen %}chosen{% endif %} {% if result.include_override == False %}exclude{% endif %}">
            <a target="_blank" href="/image/{{ result.file_id }}">
              <div class="image-thumbnail large" title="{{ result.file_id }}">
                <img src="/image/{{ result.file_id }}"/>
              </div>
            </a>
          </span>
        </td>
        <td>
          <span class="grid">
            <a target="_blank" href="/image/cropped/{{ result.file_id }}">
              <div class="image-thumbnail large" title="{{ result.file_id }}">
                <img src="/image/cropped/{{ result.file_id }}"/>
              </div>
            </a>
          </span>
        </td>
        <td>
          <table>
            <tr>
              <th>Chosen?</th>
              <td>{{ result.is_chosen }}</td>
            </tr>
            <tr>
              <th>Override?</th>
              <td>
                <form method="POST">
                  <input type="hidden" name="file_id" value="{{ result.file_id }}"/>
                  <button type="submit" name="include_override" value="false"
                    {% if result.include_override == False %}class="selected"{% endif %}>
                    Exclude
                  </button>
                  <button type="submit" name="include_override" value="none"
                    {% if result.include_override == None %}class="selected"{% endif %}>
                    Clear
                  </button>
                  <button type="submit" name="include_override" value="true"
                    {% if result.include_override == True %}class="selected"{% endif %}>
                    Include
                  </button>
                </form>
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
        </td>
      </tr>
    {% endfor %}
  </table>
{% endblock %}
