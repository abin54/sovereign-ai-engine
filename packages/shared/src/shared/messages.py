from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid
import time

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class Message(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    trace_id: Optional[str] = None
    span_id: Optional[str] = None

class TaskRequest(Message):
    task_id: str
    skill_name: str
    action: str
    input_data: Dict[str, Any]
    priority: int = 0

class TaskResponse(Message):
    task_id: str
    status: TaskStatus
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class Heartbeat(Message):
    service_id: str
    service_type: str
    capabilities: List[str]
    status: str = "healthy"
