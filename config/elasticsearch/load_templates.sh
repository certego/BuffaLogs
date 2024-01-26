#!/bin/bash
curl -X PUT "localhost:59200/_template/example?pretty" -H 'Content-Type: application/json' -d'@./example_template.json'