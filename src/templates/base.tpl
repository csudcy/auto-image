<!doctype html>
<html>
    <head>
        <title>{% block title %}{% endblock %} - Auto Image</title>
        <link rel="stylesheet" href="/static/base.css">
        {% block extra_head %}{% endblock %}
    </head>
    <body>
        {% block content %}{% endblock %}
    </body>
</html>
