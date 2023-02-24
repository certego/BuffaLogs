#!/bin/bash

# Apply migration before starting uwsgi
python /opt/certego/buffalogs/manage.py migrate


# Manage static files
python manage.py collectstatic --noinput --clear

# Run server
uwsgi --ini /opt/certego/buffalogs/buffalogs_uwsgi.ini

