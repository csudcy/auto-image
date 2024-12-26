<!doctype html>
<html>
    <head>
        <title>{% block title %}{% endblock %} - Auto Image</title>
        <link rel="stylesheet" href="//cdn.datatables.net/2.1.8/css/dataTables.dataTables.min.css">
        <link rel="stylesheet" href="/static/main.css">
        <script type="text/javascript" src="//code.jquery.com/jquery-3.7.1.min.js"></script>
        <script type="text/javascript" src="//cdn.datatables.net/2.1.8/js/dataTables.min.js"></script>
        <script type="text/javascript" src="/static/main.js"></script>
    </head>
    <body>
        {% block content %}{% endblock %}
    </body>
</html>
