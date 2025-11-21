import json, time, threading, random
from .redis_client import get_redis
from .settings import WORKER_ID, HB_TTL_S, HB_PERIOD_S

r = get_redis()
QUEUE_KEY = "queue:tasks"
INFLIGHT = "inflight"

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
    threading.Thread(target=heartbeat_loop, daemon=True).start()
    while True:
        item = r.brpop(QUEUE_KEY, timeout=5)
        if not item:
            continue
        _, raw = item
        msg = json.loads(raw)
        task_id = msg["task_id"]
        payload = msg.get("payload")
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

            result = do_work(payload)

            pipe = r.pipeline(True)
            pipe.hset(tkey, mapping={
                "status": "done",
                "result": json.dumps(result),
                "updated_at": time.time(),
            })
            pipe.srem(INFLIGHT, task_id)
            pipe.execute()
        except Exception as e:
            pipe = r.pipeline(True)
            pipe.hset(tkey, mapping={
                "status": "failed",
                "error": str(e),
                "updated_at": time.time(),
            })
            pipe.srem(INFLIGHT, task_id)
            pipe.execute()

if __name__ == "__main__":
    main()
