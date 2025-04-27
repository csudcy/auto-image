<!doctype html>
<html>
    <head>
        <title>{% block title %}{% endblock %} - Auto Image</title>
        <link rel="stylesheet" href="/static/base.css">
        {% block extra_head %}{% endblock %}
    </head>
    <body>
        <header>
            <nav>
                <a class="button" href="/">Home</a>
                <a class="button" href="/grid">Images</a>
                <a class="button" href="/map">Map</a>
                <a class="button" href="/processing">Processing</a>
            </nav>
        </header>
        <main>
            {% block content %}{% endblock %}
        </main>
    </body>
</html>
