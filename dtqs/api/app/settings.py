from pydantic import BaseModel
import os

class Settings(BaseModel):
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    task_timeout_s: int = int(os.getenv("TASK_TIMEOUT_S", 30))   # per-task soft timeout (reserved)
    hb_ttl_s: int = int(os.getenv("HB_TTL_S", 10))               # worker heartbeat TTL
    watchdog_period_s: int = int(os.getenv("WATCHDOG_PERIOD_S", 5))
    max_retries: int = int(os.getenv("MAX_RETRIES", 3))

settings = Settings()
