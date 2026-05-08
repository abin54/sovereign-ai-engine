from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field
import asyncio

class TaskNode(BaseModel):
    id: str
    skill_name: str
    action: str
    input_template: Dict[str, Any]
    dependencies: List[str] = Field(default_factory=list)
    output_schema: Optional[Dict[str, Any]] = None
    timeout: int = 30
    retries: int = 3

class TaskGraph(BaseModel):
    graph_id: str
    nodes: Dict[str, TaskNode]
    
    def get_execution_order(self) -> List[List[str]]:
        """Returns nodes in topological order, grouped by parallelizable levels."""
        levels = []
        visited = set()
        remaining = set(self.nodes.keys())
        
        while remaining:
            current_level = []
            for node_id in list(remaining):
                node = self.nodes[node_id]
                if all(dep in visited for dep in node.dependencies):
                    current_level.append(node_id)
            
            if not current_level:
                # Circular dependency or missing dependency
                raise ValueError("Graph has circular dependencies or missing nodes.")
            
            levels.append(current_level)
            visited.update(current_level)
            remaining.difference_update(current_level)
            
        return levels

class GraphInstance(BaseModel):
    graph_id: str
    instance_id: str
    task_states: Dict[str, Dict[str, Any]] = Field(default_factory=dict) # node_id -> {status, output, etc.}
    
    def update_node(self, node_id: str, status: str, output: Optional[Any] = None, error: Optional[str] = None):
        self.task_states[node_id] = {
            "status": status,
            "output": output,
            "error": error,
            "timestamp": asyncio.get_event_loop().time()
        }
