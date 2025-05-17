#!/usr/bin/env bash
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d
sleep 5
docker exec naijapulsebot python src/healthcheck.py
if [ $? -eq 0 ]; then echo "STAGING OK"; else echo "STAGING FAILED"; exit 1; fi 