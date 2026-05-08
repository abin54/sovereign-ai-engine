import asyncio
import uuid
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
            # Execute nodes in parallel at this level
            tasks = [self.execute_node(graph.nodes[node_id], instance) for node_id in level]
            await asyncio.gather(*tasks)
            
        self.logger.info(f"Graph execution complete: {graph.graph_id}", instance_id=instance_id)
        return instance

    async def execute_node(self, node: TaskNode, instance: GraphInstance):
        task_id = f"{instance.instance_id}_{node.id}"
        instance.update_node(node.id, TaskStatus.RUNNING)
        
        # Prepare input data (resolve templates from dependencies)
        input_data = self._resolve_input(node.input_template, instance)
        
        request = TaskRequest(
            task_id=task_id,
            skill_name=node.skill_name,
            action=node.action,
            input_data=input_data
        )
        
        self.logger.info(f"Dispatching task {node.id} to {node.skill_name}", node_id=node.id, skill_name=node.skill_name)
        
        # Publish to the skill's topic
        topic = f"tasks.{node.skill_name}"
        self.bus.publish(topic, request)
        
        # Wait for response (simplified: in a real system, this would be another subscriber)
        # For the sake of this example, we'll wait on a specific response topic
        response = await self._wait_for_response(task_id)
        
        if response.status == TaskStatus.COMPLETED:
            instance.update_node(node.id, TaskStatus.COMPLETED, output=response.output_data)
        else:
            instance.update_node(node.id, TaskStatus.FAILED, error=response.error)
            raise RuntimeError(f"Task {node.id} failed: {response.error}")

    def _resolve_input(self, template: Dict[str, Any], instance: GraphInstance) -> Dict[str, Any]:
        # Simple resolution logic: if a value starts with $, it's a reference to a dependency output
        # e.g. "$node_a.result_key"
        resolved = {}
        for k, v in template.items():
            if isinstance(v, str) and v.startswith("$"):
                parts = v[1:].split(".")
                node_id = parts[0]
                key = parts[1] if len(parts) > 1 else "output"
                resolved[k] = instance.task_states[node_id]["output"].get(key)
            else:
                resolved[k] = v
        return resolved

    async def _wait_for_response(self, task_id: str) -> TaskResponse:
        # Mocking the wait for now. In a real system, this would subscribe to a response topic.
        await asyncio.sleep(2)
        return TaskResponse(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            output_data={"result": "Success from skill"}
        )

if __name__ == "__main__":
    bus = MessageBus()
    orch = Orchestrator(bus)
    
    # Example Graph: Security Scan then ML Analysis
    nodes = {
        "scan": TaskNode(id="scan", skill_name="security", action="scan_code", input_template={"path": "./"}),
        "analyze": TaskNode(id="analyze", skill_name="ml", action="analyze_report", 
                            dependencies=["scan"], input_template={"report": "$scan.result"})
    }
    graph = TaskGraph(graph_id="security_ml_workflow", nodes=nodes)
    
    asyncio.run(orch.execute_graph(graph))
