import asyncio
import json
import threading
import time
from typing import Any, Dict, Optional
from .bus import MessageBus
from .messages import TaskRequest, TaskResponse, TaskStatus, Heartbeat
from .telemetry import setup_telemetry, StructuredLogger

class BaseSkill:
    def __init__(self, skill_name: str, bus: MessageBus):
        self.skill_name = skill_name
        self.bus = bus
        self.service_id = f"{skill_name}-{int(time.time())}"
        self.logger = StructuredLogger(skill_name)
        setup_telemetry(skill_name)
        self.stop_event = threading.Event()

    def start(self):
        self.logger.info(f"Starting skill: {self.skill_name}", service_id=self.service_id)
        
        # Start heartbeat thread
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()
        
        # Start listening for tasks
        topic = f"tasks.{self.skill_name}"
        self.bus.subscribe(topic, f"{self.skill_name}_group", self.service_id, self._handle_task_raw)

    def _heartbeat_loop(self):
        while not self.stop_event.is_set():
            heartbeat = Heartbeat(
                service_id=self.service_id,
                service_type=self.skill_name,
                capabilities=self.get_capabilities()
            )
            self.bus.register_service(self.service_id, heartbeat.model_dump())
            time.sleep(30)

    def _handle_task_raw(self, message: Any):
        # Redis Stream message data is in message.data
        try:
            task_request = TaskRequest.model_validate_json(message.data["data"])
            self.logger.info(f"Received task: {task_request.task_id}", task_id=task_request.task_id)
            
            # Execute task
            result = self.handle_task(task_request)
            
            # Send response
            response = TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                output_data=result
            )
            # In a real system, publish to a response topic or the caller's specific queue
            self.bus.publish(f"responses.{task_request.task_id}", response)
            
        except Exception as e:
            self.logger.error(f"Error handling task: {e}", task_id=getattr(task_request, 'task_id', 'unknown'))
            # Send error response
            if 'task_request' in locals():
                response = TaskResponse(
                    task_id=task_request.task_id,
                    status=TaskStatus.FAILED,
                    error=str(e)
                )
                self.bus.publish(f"responses.{task_request.task_id}", response)

    def handle_task(self, request: TaskRequest) -> Dict[str, Any]:
        """Override this in subclasses."""
        raise NotImplementedError

    def get_capabilities(self) -> list[str]:
        """Override this in subclasses."""
        return []
