import asyncio
import json
import time
from typing import Any, Dict, Optional, List
from .bus import MessageBus
from .messages import TaskRequest, TaskResponse, TaskStatus, Heartbeat
from .telemetry import setup_telemetry, StructuredLogger
from .executor import SandboxToolExecutor
from .security import ToolPermissions, Capability

class BaseSkill:
    def __init__(self, skill_name: str, bus: MessageBus):
        self.skill_name = skill_name
        self.bus = bus
        self.service_id = f"{skill_name}-{int(time.time())}"
        self.logger = StructuredLogger(skill_name)
        self.executor = SandboxToolExecutor()
        setup_telemetry(skill_name)
        self.stop_event = asyncio.Event()

    async def start(self):
        self.logger.info(f"Starting skill: {self.skill_name}", service_id=self.service_id)
        
        # Start heartbeat and task subscription
        await asyncio.gather(
            self._heartbeat_loop(),
            self._listen_for_tasks()
        )

    async def _listen_for_tasks(self):
        topic = f"tasks.{self.skill_name}"
        await self.bus.subscribe(topic, f"{self.skill_name}_group", self.service_id, self._handle_task_raw)

    async def _heartbeat_loop(self):
        while not self.stop_event.is_set():
            heartbeat = Heartbeat(
                service_id=self.service_id,
                service_type=self.skill_name,
                capabilities=self.get_capabilities()
            )
            await self.bus.register_service(self.service_id, heartbeat.model_dump())
            await asyncio.sleep(30)

    async def _handle_task_raw(self, message: Any):
        try:
            task_request = TaskRequest.model_validate_json(message.data["data"])
            self.logger.info(f"Received task: {task_request.task_id}", task_id=task_request.task_id)
            
            # Execute task
            result = await self.handle_task(task_request)
            
            # Send response
            response = TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                output_data=result
            )
            await self.bus.publish(f"responses.{task_request.task_id}", response)
            
        except Exception as e:
            self.logger.error(f"Error handling task: {e}", task_id=getattr(task_request, 'task_id', 'unknown'))
            if 'task_request' in locals():
                response = TaskResponse(
                    task_id=task_request.task_id,
                    status=TaskStatus.FAILED,
                    error=str(e)
                )
                await self.bus.publish(f"responses.{task_request.task_id}", response)

    async def handle_task(self, request: TaskRequest) -> Dict[str, Any]:
        """Override this in subclasses."""
        raise NotImplementedError

    def get_capabilities(self) -> List[str]:
        """Override this in subclasses."""
        return []
