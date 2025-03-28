#!/bin/bash

# Define credentials
ELASTIC_USERNAME="elastic"
ELASTIC_PASSWORD="qwzhB2eeNKvRTgnenzyR"

# Load the template with authentication
curl -u $ELASTIC_USERNAME:$ELASTIC_PASSWORD -X PUT "http://localhost:9200/_template/example?pretty" \
     -H "Content-Type: application/json" \
     -d @./example_template.json
