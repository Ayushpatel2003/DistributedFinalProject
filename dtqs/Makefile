SHELL := /bin/bash

.PHONY: up down restart ps scale logs logs-api logs-worker metrics-api metrics-worker submit-test submit-batch submit-mixed stop-worker

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

# Submit a batch of 10 numeric tasks (1..10) to drive load.
submit-batch:
	for i in {1..10}; do \
		curl -s -X POST http://localhost:8000/tasks -H 'Content-Type: application/json' -d "{\"payload\": $$i}\"; \
		echo; \
	done

# Submit a mixed batch including a crash to exercise failure metrics.
submit-mixed:
	for p in 2 4 6 crash 8 10; do \
		curl -s -X POST http://localhost:8000/tasks -H 'Content-Type: application/json' -d "{\"payload\": \"$$p\"}"; \
		echo; \
	done

stop-worker:
	docker compose stop worker
