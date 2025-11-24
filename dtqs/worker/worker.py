import json, time, threading, random
from .redis_client import get_redis
from .settings import WORKER_ID, HB_TTL_S, HB_PERIOD_S
from prometheus_client import Counter, Gauge, Histogram, start_http_server

r = get_redis()
QUEUE_KEY = "queue:tasks"
INFLIGHT = "inflight"
TASKS_COMPLETED = Counter("dtqs_tasks_completed_total", "Tasks completed")
TASKS_FAILED = Counter("dtqs_tasks_failed_total", "Tasks that failed")
TASK_QUEUE_WAIT_SECONDS = Histogram(
    "dtqs_task_queue_wait_seconds", "Seconds a task waited in queue before start", buckets=(0.1, 0.5, 1, 2, 5, 10, 30)
)
TASK_LATENCY_SECONDS = Histogram(
    "dtqs_task_latency_seconds", "Seconds to process a task", buckets=(0.1, 0.5, 1, 2, 5, 10, 30)
)
INFLIGHT_GAUGE = Gauge("dtqs_tasks_in_progress", "Tasks currently being processed by this worker")
METRIC_COMPLETED_KEY = "metrics:tasks_completed_total"
METRIC_FAILED_KEY = "metrics:tasks_failed_total"

def do_work(payload):
    # Example workload: if number → square it; otherwise echo
    delay = random.uniform(0.5, 2.0)
    time.sleep(delay)
    if payload == "crash":
        raise RuntimeError("simulated failure")
    if isinstance(payload, (int, float)):
        return payload * payload
    return {"echo": payload}

def heartbeat_loop():
    hb_key = f"worker:hb:{WORKER_ID}"
    while True:
        try:
            r.set(hb_key, "1", ex=HB_TTL_S)
        except Exception:
            pass
        time.sleep(HB_PERIOD_S)

def main():
    # Load persisted counters from Redis so metrics survive worker restarts.
    try:
        persisted_completed = int(r.get(METRIC_COMPLETED_KEY) or 0)
        persisted_failed = int(r.get(METRIC_FAILED_KEY) or 0)
        if persisted_completed:
            TASKS_COMPLETED.inc(persisted_completed)
        if persisted_failed:
            TASKS_FAILED.inc(persisted_failed)
    except Exception:
        pass

    start_http_server(8001)
    threading.Thread(target=heartbeat_loop, daemon=True).start()
    while True:
        item = r.brpop(QUEUE_KEY, timeout=5)
        if not item:
            continue
        _, raw = item
        msg = json.loads(raw)
        task_id = msg["task_id"]
        payload = msg.get("payload")
        enqueued_at = msg.get("enqueued_at")
        started_at = time.time()
        tkey = f"task:{task_id}"
        try:
            pipe = r.pipeline(True)
            pipe.hset(tkey, mapping={
                "status": "in_progress",
                "worker": WORKER_ID,
                "updated_at": time.time(),
            })
            pipe.sadd(INFLIGHT, task_id)
            pipe.execute()
            try:
                INFLIGHT_GAUGE.set(r.scard(INFLIGHT))
            except Exception:
                pass

            result = do_work(payload)
            duration = time.time() - started_at
            if enqueued_at:
                try:
                    queue_wait = max(0.0, started_at - float(enqueued_at))
                    TASK_QUEUE_WAIT_SECONDS.observe(queue_wait)
                except Exception:
                    pass

            pipe = r.pipeline(True)
            pipe.hset(tkey, mapping={
                "status": "done",
                "result": json.dumps(result),
                "updated_at": time.time(),
            })
            pipe.srem(INFLIGHT, task_id)
            pipe.incr(METRIC_COMPLETED_KEY)
            pipe.execute()
            TASKS_COMPLETED.inc()
            TASK_LATENCY_SECONDS.observe(duration)
        except Exception as e:
            pipe = r.pipeline(True)
            pipe.hset(tkey, mapping={
                "status": "failed",
                "error": str(e),
                "updated_at": time.time(),
            })
            pipe.srem(INFLIGHT, task_id)
            pipe.incr(METRIC_FAILED_KEY)
            pipe.execute()
            TASKS_FAILED.inc()
        try:
            INFLIGHT_GAUGE.set(r.scard(INFLIGHT))
        except Exception:
            pass

if __name__ == "__main__":
    main()
