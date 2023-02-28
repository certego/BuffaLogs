#!/bin/bash
curl -X PUT "127.0.0.1:44519/_template/example?pretty" -H 'Content-Type: application/json' -d'@./config/elasticsearch/example_template.json'