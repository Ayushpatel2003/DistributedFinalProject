import os
WORKER_ID = os.getenv("WORKER_ID") or os.getenv("HOSTNAME", "worker-unknown")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
HB_TTL_S = int(os.getenv("HB_TTL_S", 10))
HB_PERIOD_S = int(os.getenv("HB_PERIOD_S", 3))
