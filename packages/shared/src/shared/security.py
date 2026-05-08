from typing import List, Optional
from pydantic import BaseModel
import enum

class Capability(str, enum.Enum):
    FS_READ = "fs:read"
    FS_WRITE = "fs:write"
    NET_OUTBOUND = "net:outbound"
    SHELL_EXEC = "shell:exec"
    GITHUB_WRITE = "github:write"

class ToolPermissions(BaseModel):
    allowed_capabilities: List[Capability]
    resource_limits: Optional[Dict[str, Any]] = None # e.g., {"cpu": 0.5, "mem": "512MB"}

class AuditLog(BaseModel):
    timestamp: float
    caller_id: str
    tool_name: str
    arguments: Dict[str, Any]
    capabilities_used: List[Capability]
    result_summary: str
    success: bool

class ToolExecutorInterface:
    async def execute(self, tool_name: str, args: Dict[str, Any], permissions: ToolPermissions) -> Any:
        raise NotImplementedError
