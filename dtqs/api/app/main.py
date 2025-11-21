from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from .redis_client import get_redis
from .models import TaskSubmit, TaskStatus
from .settings import settings
from prometheus_client import Counter, Gauge, generate_latest
import json, time, threading

app = FastAPI(title="DTQS Scheduler")
r = get_redis()

# Metrics
TASKS_SUBMITTED = Counter("dtqs_tasks_submitted_total", "Tasks submitted")
TASKS_COMPLETED = Counter("dtqs_tasks_completed_total", "Tasks completed")
TASKS_RETRIED   = Counter("dtqs_tasks_retried_total", "Tasks retried")
QUEUE_DEPTH     = Gauge("dtqs_queue_depth", "Current queue length")

QUEUE_KEY = "queue:tasks"
INFLIGHT = "inflight"

@app.post("/tasks", response_model=TaskStatus)
def submit_task(ts: TaskSubmit):
    task_id = ts.task_id
    now = time.time()
    pipe = r.pipeline(True)
    # record initial task state (store payload too for safe requeue)
    pipe.hset(f"task:{task_id}", mapping={
        "status": "queued",
        "retries": 0,
        "updated_at": now,
        "payload": json.dumps(ts.payload),
    })
    pipe.lpush(QUEUE_KEY, json.dumps({"task_id": task_id, "payload": ts.payload}))
    pipe.execute()
    TASKS_SUBMITTED.inc()
    try:
        QUEUE_DEPTH.set(r.llen(QUEUE_KEY))
    except Exception:
        pass
    return TaskStatus(task_id=task_id, status="queued")

@app.get("/tasks/{task_id}", response_model=TaskStatus)
def get_status(task_id: str):
    data = r.hgetall(f"task:{task_id}")
    if not data:
        raise HTTPException(404, "Task not found")
    # decode result if present
    result = data.get("result")
    try:
        result = json.loads(result) if result else None
    except Exception:
        pass
    return TaskStatus(
        task_id=task_id,
        status=data.get("status", "unknown"),
        result=result,
        error=data.get("error"),
        worker=data.get("worker"),
        retries=int(data.get("retries", 0)),
    )

@app.get("/metrics")
def metrics():
    try:
        QUEUE_DEPTH.set(r.llen(QUEUE_KEY))
    except Exception:
        pass
    return PlainTextResponse(generate_latest(), media_type="text/plain; version=0.0.4")

def watchdog_loop():
    while True:
        try:
            for task_id in list(r.smembers(INFLIGHT)):
                tkey = f"task:{task_id}"
                data = r.hgetall(tkey)
                if not data:
                    r.srem(INFLIGHT, task_id)
                    continue
                worker = data.get("worker")
                if not worker:
                    continue
                hb_key = f"worker:hb:{worker}"
                if r.ttl(hb_key) <= 0:  # worker likely dead
                    if data.get("status") == "in_progress":
                        retries = int(data.get("retries", 0))
                        if retries < settings.max_retries:
                            payload_raw = data.get("payload")
                            try:
                                payload = json.loads(payload_raw) if payload_raw else None
                            except Exception:
                                payload = payload_raw
                            r.hset(tkey, mapping={
                                "status": "queued",
                                "worker": "",
                                "updated_at": time.time(),
                                "retries": retries + 1,
                            })
                            r.lpush(QUEUE_KEY, json.dumps({"task_id": task_id, "payload": payload}))
                            r.srem(INFLIGHT, task_id)
                            TASKS_RETRIED.inc()
                        else:
                            r.hset(tkey, mapping={
                                "status": "failed",
                                "error": "max retries exceeded",
                                "updated_at": time.time(),
                            })
                            r.srem(INFLIGHT, task_id)
        except Exception:
            pass
        time.sleep(settings.watchdog_period_s)

threading.Thread(target=watchdog_loop, daemon=True).start()
