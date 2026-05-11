import asyncio
import json
import time
import http.server
import threading
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
        self.failure_count = 0
        self.is_healthy = True

    async def start(self):
        self.logger.info(f"Starting skill: {self.skill_name}", service_id=self.service_id)
        
        # Start health check, heartbeat and task subscription
        await asyncio.gather(
            self._heartbeat_loop(),
            self._listen_for_tasks(),
            self._run_health_server()
        )

    async def _listen_for_tasks(self):
        topic = f"tasks.{self.skill_name}"
        await self.bus.subscribe(topic, f"{self.skill_name}_group", self.service_id, self._handle_task_raw, stop_event=self.stop_event)

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
            
            # Reset circuit breaker on success
            self.failure_count = 0
            self.is_healthy = True
            
            # Send response
            response = TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                output_data=result
            )
            await self.bus.publish(f"responses.{task_request.task_id}", response)
            
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"Error handling task: {e} (Failure {self.failure_count})", 
                              task_id=getattr(task_request, 'task_id', 'unknown'))
            
            # Circuit breaker logic
            if self.failure_count >= 5:
                self.is_healthy = False
                self.logger.warning(f"Circuit Breaker Triggered: Skill {self.skill_name} is now UNHEALTHY")

            if 'task_request' in locals():
                # Move to Dead Letter Queue (DLQ)
                dlq_topic = f"dlq.tasks.{self.skill_name}"
                await self.bus.publish(dlq_topic, task_request)
                
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

    async def _run_health_server(self):
        """Starts a minimal HTTP server for health probes."""
        skill = self
        
        class HealthHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/health":
                    status_code = 200 if skill.is_healthy else 503
                    self.send_response(status_code)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "status": "healthy" if skill.is_healthy else "degraded",
                        "failures": skill.failure_count,
                        "skill": skill.skill_name
                    }).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def log_message(self, format, *args):
                return # Quiet logs

        # Find a port (e.g., 8080 + hash of skill name)
        # For MVP, we'll use a fixed port or env var
        import os
        port = int(os.environ.get(f"HEALTH_PORT_{self.skill_name.upper().replace('-', '_')}", 8080))
        
        server = http.server.HTTPServer(("0.0.0.0", port), HealthHandler) # nosec B104
        self.logger.info(f"Health check server started on port {port}", port=port)
        
        # Run in a thread to not block asyncio (though we could use an async server)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        
        while not self.stop_event.is_set():
            await asyncio.sleep(1)
        
        server.shutdown()
