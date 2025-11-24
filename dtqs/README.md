# DTQS – Distributed Task Queue & Scheduler

A minimal distributed task queue built with FastAPI (API + scheduler), Redis (broker/state), and worker containers. Includes Prometheus metrics and optional Grafana.

## Stack
- FastAPI / uvicorn
- Redis
- Worker process (Python)
- Prometheus (scrapes `/metrics`)
- Grafana (optional)
- Docker Compose orchestration

## Quick start
```bash
cd /Users/ayush/Desktop/DistributedFinalProject/dtqs
docker compose up --build
# or run detached
# docker compose up -d --build
```

Check status:
```bash
docker compose ps
```

## Submit and check a task
```bash
# submit
curl -X POST http://localhost:8000/tasks \
  -H 'Content-Type: application/json' \
  -d '{"payload": 12}'
# => {"task_id":"<ID>","status":"queued",...}

# poll status
curl http://localhost:8000/tasks/<ID>
# queued → in_progress → done (result is payload squared if numeric)
```

## Failures and retries
- Submit a failing task: payload `"crash"` will raise an error.
- If a worker dies (stop it with `docker compose stop worker`), watchdog requeues in-progress tasks after the heartbeat TTL until `MAX_RETRIES` is reached.

## Metrics
- API metrics endpoint: `http://localhost:8000/metrics`
- Prometheus UI: `http://localhost:9090`
- Useful queries:
  - `dtqs_queue_depth`
  - `dtqs_tasks_submitted_total`
  - `dtqs_tasks_retried_total`
  - `rate(dtqs_tasks_completed_total[1m])` (if wired)
  - `rate(dtqs_tasks_retried_total[1m])`

## Scaling workers
```bash
docker compose up -d --scale worker=3
```

## Stop the stack
```bash
docker compose down -v
```

## Notes
- Task status and results live in Redis keys `task:{id}`.
- Heartbeats: `worker:hb:{worker_id}` with TTL controls watchdog requeues.
- Queue key: `queue:tasks`; inflight set: `inflight`.
