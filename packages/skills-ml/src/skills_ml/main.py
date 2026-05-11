import asyncio
import os
from typing import Any, Dict, List
from shared.skill import BaseSkill
from shared.bus import MessageBus
from shared.messages import TaskRequest
from shared.llm import LLMFactory, LLMRequest, LLMMessage
from shared.config import settings

class MLSkill(BaseSkill):
    def __init__(self, bus: MessageBus):
        super().__init__("ml", bus)
        self.llm = LLMFactory.get_provider("openai", settings.openai_api_key)

    def get_capabilities(self) -> List[str]:
        return []

    async def handle_task(self, request: TaskRequest) -> Dict[str, Any]:
        action = request.action
        args = request.input_data
        
        if action == "analyze_report":
            content = args.get("report")
            self.logger.info("Analyzing report with LLM...")
            
            prompt = f"Analyze the following security report and summarize findings:\n\n{content}"
            llm_req = LLMRequest(messages=[LLMMessage(role="user", content=prompt)], model="gpt-4")
            llm_res = await self.llm.generate(llm_req)
            
            return {"summary": llm_res.content, "usage": llm_res.usage}
        
        elif action == "classify":
            text = args.get("text")
            self.logger.info(f"Classifying text with LLM: {text[:50]}...")
            
            prompt = f"Classify the following text into 'security', 'ml', or 'other'. Return ONLY the category name.\n\nText: {text}"
            llm_req = LLMRequest(messages=[LLMMessage(role="user", content=prompt)], model="gpt-3.5-turbo")
            llm_res = await self.llm.generate(llm_req)
            
            return {"category": llm_res.content.strip().lower(), "usage": llm_res.usage}
        
        elif action == "generate_text":
            prompt = args.get("prompt")
            llm_req = LLMRequest(messages=[LLMMessage(role="user", content=prompt)], model="gpt-4")
            llm_res = await self.llm.generate(llm_req)
            return {"text": llm_res.content}
        
        else:
            raise ValueError(f"Unknown action '{action}' for MLSkill")

async def main():
    bus = MessageBus()
    skill = MLSkill(bus)
    await skill.start()

if __name__ == "__main__":
    asyncio.run(main())
