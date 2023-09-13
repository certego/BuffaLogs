=========
BuffaLogs
=========

BuffaLogs is a Django app whose main purpose is to detect anomaly logins.

Detaild documentation is in the ``docs/`` directory.

Quick start
-----------

1. Add "buffalogs" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...,
        "buffalogs",
    ]

2. Include the buffalogs URLconf in your project urls.py like this::

    path("buffalogs/", include("buffalogs.urls")),

3. Run ``python manage.py migrate`` to create the BuffaLogs models.

4. Start the development server and visit http://127.0.0.1:8000/admin/
   to analyze th eBuffaLogs detections (you'll need the Admin app enabled with ``python manage.py runserver``).

5. Visit http://127.0.0.1:8000/ to visualize the BuffaLogs interface.