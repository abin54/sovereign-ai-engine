import asyncio
from typing import Any, Dict, List
from shared.skill import BaseSkill
from shared.bus import MessageBus
from shared.messages import TaskRequest
from shared.security import ToolPermissions, Capability

class MemorySkill(BaseSkill):
    def __init__(self, bus: MessageBus):
        super().__init__("memory", bus)
        self.storage: Dict[str, Any] = {}

    def get_capabilities(self) -> List[str]:
        return []

    async def handle_task(self, request: TaskRequest) -> Dict[str, Any]:
        action = request.action
        args = request.input_data
        
        permissions = ToolPermissions(allowed_capabilities=[])

        if action == "store":
            key = args.get("key")
            value = args.get("value")
            if not key:
                raise ValueError("Missing 'key' for store action")
            self.storage[key] = value
            self.logger.info(f"Stored data for key: {key}")
            return {"status": "success", "key": key}
        
        elif action == "retrieve":
            key = args.get("key")
            if not key:
                raise ValueError("Missing 'key' for retrieve action")
            value = self.storage.get(key)
            self.logger.info(f"Retrieved data for key: {key}")
            return {"value": value, "exists": key in self.storage}
        
        else:
            raise ValueError(f"Unknown action '{action}' for MemorySkill")

async def main():
    bus = MessageBus()
    skill = MemorySkill(bus)
    await skill.start()

if __name__ == "__main__":
    asyncio.run(main())
