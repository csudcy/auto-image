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
                <a href="/">Home</a>
                <a href="/grid">Images</a>
                <a href="/processing">Processing</a>
            </nav>
        </header>
        <main>
            {% block content %}{% endblock %}
        </main>
    </body>
</html>
