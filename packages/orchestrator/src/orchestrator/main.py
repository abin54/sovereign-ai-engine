import asyncio
import uuid
import json
from typing import Any, Dict, List
from shared.bus import MessageBus
from shared.messages import TaskRequest, TaskResponse, TaskStatus
from shared.dag import TaskGraph, GraphInstance, TaskNode
from shared.telemetry import setup_telemetry, StructuredLogger

class Orchestrator:
    def __init__(self, bus: MessageBus):
        self.bus = bus
        self.logger = StructuredLogger("orchestrator")
        self.active_graphs: Dict[str, GraphInstance] = {}
        setup_telemetry("orchestrator")

    async def execute_graph(self, graph: TaskGraph):
        instance_id = str(uuid.uuid4())
        instance = GraphInstance(graph_id=graph.graph_id, instance_id=instance_id)
        self.active_graphs[instance_id] = instance
        
        self.logger.info(f"Starting graph execution: {graph.graph_id}", graph_id=graph.graph_id, instance_id=instance_id)
        
        execution_levels = graph.get_execution_order()
        for level in execution_levels:
            tasks = [self.execute_node(graph.nodes[node_id], instance) for node_id in level]
            await asyncio.gather(*tasks)
            
        self.logger.info(f"Graph execution complete: {graph.graph_id}", instance_id=instance_id)
        return instance

    async def execute_node(self, node: TaskNode, instance: GraphInstance):
        task_id = f"{instance.instance_id}_{node.id}"
        
        input_data = self._resolve_input(node.input_template, instance)
        
        request = TaskRequest(
            task_id=task_id,
            skill_name=node.skill_name,
            action=node.action,
            input_data=input_data
        )
        
        max_retries = node.retries
        for attempt in range(max_retries + 1):
            try:
                instance.update_node(node.id, TaskStatus.RUNNING)
                self.logger.info(f"Dispatching task {node.id} to {node.skill_name} (Attempt {attempt+1}/{max_retries+1})", 
                                  node_id=node.id, skill_name=node.skill_name)
                
                topic = f"tasks.{node.skill_name}"
                await self.bus.publish(topic, request)
                
                response = await self._wait_for_response(task_id, timeout=node.timeout * 1000)
                
                if response.status == TaskStatus.COMPLETED:
                    instance.update_node(node.id, TaskStatus.COMPLETED, output=response.output_data)
                    return
                else:
                    raise RuntimeError(f"Task {node.id} failed: {response.error}")
            
            except Exception as e:
                self.logger.error(f"Error executing node {node.id}: {e}")
                if attempt < max_retries:
                    wait_time = 2 ** attempt # Exponential backoff
                    self.logger.info(f"Retrying node {node.id} in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    instance.update_node(node.id, TaskStatus.FAILED, error=str(e))
                    raise

    def _resolve_input(self, template: Dict[str, Any], instance: GraphInstance) -> Dict[str, Any]:
        resolved = {}
        for k, v in template.items():
            if isinstance(v, str) and v.startswith("$"):
                parts = v[1:].split(".")
                node_id = parts[0]
                key = parts[1] if len(parts) > 1 else "output"
                # Handle cases where output might be a dict or a string
                node_state = instance.task_states.get(node_id, {})
                node_output = node_state.get("output", {})
                if isinstance(node_output, dict):
                    resolved[k] = node_output.get(key, node_output)
                else:
                    resolved[k] = node_output
            else:
                resolved[k] = v
        return resolved

    async def _wait_for_response(self, task_id: str, timeout: int = 60000) -> TaskResponse:
        """Waits for a response on the response stream using event-driven subscription."""
        topic = f"responses.{task_id}"
        self.logger.info(f"Waiting for response on {topic}...")
        
        message_data = await self.bus.receive(topic, timeout=timeout)
        if message_data:
            return TaskResponse.model_validate_json(message_data["data"])
        
        return TaskResponse(task_id=task_id, status=TaskStatus.FAILED, error="Timeout waiting for response")
