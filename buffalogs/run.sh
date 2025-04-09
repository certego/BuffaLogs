#!/bin/bash

# Change the working directory
cd /opt/certego/buffalogs/

# Apply migration before starting uwsgi
python manage.py migrate

# Manage static files
python manage.py collectstatic --noinput --clear

# Run server
uwsgi --ini buffalogs_uwsgi.ini

