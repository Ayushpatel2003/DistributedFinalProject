# DTQS – Distributed Task Queue & Scheduler

Stack: FastAPI, Redis, Docker Compose, Prometheus (+ optional Grafana)

## Run
```bash
docker compose up --build
# scale workers
docker compose up -d --scale worker=3
```

Submit Tasks
curl -X POST http://localhost:8000/tasks \
  -H 'Content-Type: application/json' \
  -d '{"payload": 12}'
# => {"task_id":"<ID>","status":"queued"}

curl http://localhost:8000/tasks/<ID>
# queued -> in_progress -> done

Simulate Failure
# task that raises an error
curl -X POST http://localhost:8000/tasks \
  -H 'Content-Type: application/json' \
  -d '{"payload": "crash"}'

# or kill workers:
docker compose stop worker
# after ~HB_TTL_S, watchdog requeues; then:
docker compose up -d --scale worker=3

Monitoring


Prometheus: http://localhost:9090


Grafana: http://localhost:3000 (add Prometheus datasource http://prometheus:9090)


Metrics:


rate(dtqs_tasks_submitted_total[1m])


rate(dtqs_tasks_completed_total[1m])


rate(dtqs_tasks_retried_total[1m])


dtqs_queue_depth




Notes


Worker heartbeats stored at worker:hb:{worker_id} with TTL.


Watchdog requeues in_progress tasks whose worker heartbeat expired, up to MAX_RETRIES.


Results and status are authoritative in task:{id}.


Extend with Redis Streams + consumer groups for at-least-once delivery.



---

### How to respond
1. Create all files exactly as above.
2. Do not paraphrase or shorten file contents.
3. After creating, run `docker compose up --build` locally.
4. Provide me with a summary of successful build output and how to submit a sample task.
5. If any step fails, fix and retry automatically until the stack starts cleanly.
6. Confirm that Prometheus scrapes `/metrics` and that `dtqs_queue_depth` updates when tasks are added.

**End of prompt.**
