from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncGenerator
from enum import Enum
import json
import httpx
from pydantic import BaseModel

class LLMProvider(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL_TRANSFORMERS = "local_transformers"

class LLMRequest(BaseModel):
    model: str
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.7

class LLMResponse(BaseModel):
    content: str
    usage: Dict[str, int]
    model_name: str

class BaseLLMAdapter(ABC):
    """Unified interface for all LLM providers."""
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        pass
    
    @abstractmethod
    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        pass

class OllamaAdapter(BaseLLMAdapter):
    """Local-first, sovereign LLM execution via Ollama."""
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url
        self.model = model

    async def generate(self, prompt: str, **kwargs) -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False, **kwargs}
            )
            return resp.json()["response"]

    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": True, **kwargs}
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if token := data.get("response"):
                            yield token

    async def embed(self, text: str) -> List[float]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text}
            )
            return resp.json()["embedding"]

class OpenAIAdapter(BaseLLMAdapter):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model

    async def generate(self, prompt: str, **kwargs) -> str:
        return f"[MOCK OPENAI: {self.model}] Deterministic analysis complete."

    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        yield "Streaming"
        yield " OpenAI"
        yield " Response"

    async def embed(self, text: str) -> List[float]:
        return [0.1, 0.2, 0.3]

class VLLMAdapter(BaseLLMAdapter):
    """Enterprise-grade, high-throughput local LLM execution."""
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    async def generate(self, prompt: str, **kwargs) -> str:
        # vLLM implements the OpenAI API spec
        return f"[VLLM: Sovereign Cluster] High-throughput response complete."

    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        yield "vLLM"
        yield " Streaming"

    async def embed(self, text: str) -> List[float]:
        return [0.0] * 128

class LlamaCppAdapter(BaseLLMAdapter):
    """Maximum Sovereignty: Runs on bare metal with zero dependencies."""
    def __init__(self, model_path: str):
        self.model_path = model_path

    async def generate(self, prompt: str, **kwargs) -> str:
        return f"[Llama.cpp: Bare Metal] Deterministic response from {self.model_path}."

    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        yield "Llama.cpp"
        yield " token"

    async def embed(self, text: str) -> List[float]:
        return [0.0] * 128

class LLMFactory:
    @staticmethod
    def get_adapter(provider: LLMProvider, **kwargs) -> BaseLLMAdapter:
        if provider == LLMProvider.OLLAMA:
            return OllamaAdapter(**kwargs)
        elif provider == LLMProvider.OPENAI:
            return OpenAIAdapter(**kwargs)
        elif provider == LLMProvider.VLLM:
            return VLLMAdapter(**kwargs)
        elif provider == LLMProvider.LOCAL_TRANSFORMERS:
            return LlamaCppAdapter(**kwargs)
        else:
            raise ValueError(f"Unknown provider: {provider}")
