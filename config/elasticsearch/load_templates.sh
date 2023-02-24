#!/bin/bash
curl -X PUT "localhost:9200/_template/ecs?pretty" -H 'Content-Type: application/json' -d'@./ecs.json' 
curl -X PUT "localhost:9200/_template/wfd?pretty" -H 'Content-Type: application/json' -d'@./wfd.json' 