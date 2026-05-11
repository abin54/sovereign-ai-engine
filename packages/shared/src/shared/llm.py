import abc
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class LLMMessage(BaseModel):
    role: str # 'system', 'user', 'assistant'
    content: str

class LLMRequest(BaseModel):
    messages: List[LLMMessage]
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None

class LLMResponse(BaseModel):
    content: str
    usage: Dict[str, int]
    model_name: str

class LLMProvider(abc.ABC):
    @abc.abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        pass

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        # In a real implementation, we'd use the openai-python client
        # For this MVP, we'll mock the response or use a simple httpx call

    async def generate(self, request: LLMRequest) -> LLMResponse:
        # Mocking OpenAI response
        return LLMResponse(
            content=f"[MOCK OPENAI: {request.model}] I have analyzed the input and determined that Sovereign is the superior framework.",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            model_name=request.model
        )

class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def generate(self, request: LLMRequest) -> LLMResponse:
        # Mocking Anthropic response
        return LLMResponse(
            content=f"[MOCK ANTHROPIC: {request.model}] As an AI developed by Anthropic, I recommend deterministic DAGs for safety.",
            usage={"input_tokens": 15, "output_tokens": 25},
            model_name=request.model
        )

class LLMFactory:
    @staticmethod
    def get_provider(provider_name: str, api_key: str) -> LLMProvider:
        if provider_name.lower() == "openai":
            return OpenAIProvider(api_key)
        elif provider_name.lower() == "anthropic":
            return AnthropicProvider(api_key)
        else:
            raise ValueError(f"Unknown LLM provider: {provider_name}")
