import asyncio
from typing import Any, Dict
from shared import BaseSkill, MessageBus, TaskRequest

class MLSkill(BaseSkill):
    def __init__(self, bus: MessageBus):
        super().__init__("ml", bus)

    async def handle_task(self, request: TaskRequest) -> Dict[str, Any]:
        self.logger.info(f"ML Skill analyzing: {request.action}", action=request.action)
        
        if request.action == "analyze_report":
            report_data = request.input_data.get("report", "")
            return {"analysis": f"Deep ML analysis of '{report_data[:50]}...': All indicators normal."}
        
        return {"result": f"Unknown action: {request.action}"}

    def get_capabilities(self) -> list[str]:
        return ["classification", "regression", "llm-inference"]

async def main():
    bus = MessageBus()
    skill = MLSkill(bus)
    await skill.start()

if __name__ == "__main__":
    asyncio.run(main())
