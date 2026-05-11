import asyncio
import os
from typing import Any, Dict, List
from shared.skill import BaseSkill
from shared.bus import MessageBus
from shared.messages import TaskRequest
from shared.security import ToolPermissions, Capability

class SecuritySkill(BaseSkill):
    def __init__(self, bus: MessageBus):
        super().__init__("security", bus)

    def get_capabilities(self) -> List[str]:
        return [Capability.FS_READ.value, Capability.SHELL_EXEC.value]

    async def handle_task(self, request: TaskRequest) -> Dict[str, Any]:
        action = request.action
        args = request.input_data
        
        # Define permissions for this skill execution
        # In a real system, these would come from the task graph or policy service
        permissions = ToolPermissions(
            allowed_capabilities=[Capability.FS_READ, Capability.SHELL_EXEC]
        )

        if action == "shell_command":
            output = await self.executor.execute("shell_command", args, permissions)
            return {"output": output}
        
        elif action == "read_file":
            path = args.get("path")
            if not path:
                raise ValueError("Missing 'path' argument for read_file action")
            
            # Use executor to read file (mocked via shell command for now or implement in executor)
            # Actually SandboxToolExecutor has a mapping for read_file but it's mocked.
            output = await self.executor.execute("read_file", {"path": path}, permissions)
            return {"content": output}
        
        else:
            raise ValueError(f"Unknown action '{action}' for SecuritySkill")

async def main():
    bus = MessageBus()
    skill = SecuritySkill(bus)
    await skill.start()

if __name__ == "__main__":
    asyncio.run(main())
