#!/bin/bash

celery -A buffalogs beat -l info --loglevel=debug