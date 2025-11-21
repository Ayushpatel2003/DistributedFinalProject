from pydantic import BaseModel, Field
from typing import Any, Optional
import uuid

class TaskSubmit(BaseModel):
    payload: Any
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class TaskStatus(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
    worker: Optional[str] = None
    retries: int = 0
