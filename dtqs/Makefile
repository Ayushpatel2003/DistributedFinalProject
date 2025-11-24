SHELL := /bin/bash

.PHONY: up down restart ps scale logs logs-api logs-worker metrics-api metrics-worker submit-test

up:
	docker compose up --build -d

down:
	docker compose down -v

restart:
	docker compose down -v && docker compose up --build -d

ps:
	docker compose ps

scale:
	docker compose up -d --scale worker=3

logs:
	docker compose logs -f --tail=200

logs-api:
	docker compose logs -f --tail=200 api

logs-worker:
	docker compose logs -f --tail=200 worker

metrics-api:
	curl -s http://localhost:8000/metrics | head

metrics-worker:
	docker compose exec prometheus wget -qO- http://worker:8001/metrics | head

submit-test:
	curl -s -X POST http://localhost:8000/tasks -H 'Content-Type: application/json' -d '{"payload": 7}' && echo
