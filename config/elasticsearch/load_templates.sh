#!/bin/bash
curl -X PUT "localhost:9200/_index_template/example?pretty" -H 'Content-Type: application/json' -d'@./example_template.json'