#!/bin/bash

celery -A buffalogs beat --schedule /tmp/celerybeat-schedule