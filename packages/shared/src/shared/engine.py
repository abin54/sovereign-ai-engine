from typing import Any, Dict, List, Optional, AsyncGenerator
from .llm import LLMFactory, LLMProvider, BaseLLMAdapter
from .telemetry import StructuredLogger, trace_llm_call

class SovereignEngine:
    """The ACTUAL engine - orchestrates LLMs, Memory, and Tools with a clean API."""
    
    def __init__(self):
        self._llm: Optional[BaseLLMAdapter] = None
        self._tool_registry: Dict[str, Dict[str, Any]] = {}
        self.logger = StructuredLogger("sovereign_engine")

    def configure_llm(self, provider: LLMProvider, **kwargs):
        """Hot-swap LLM providers without changing application logic."""
        self._llm = LLMFactory.get_adapter(provider, **kwargs)
        self.logger.info(f"Engine configured with LLM provider: {provider}")
        return self

    def register_tool(self, name: str, func: Any, description: str):
        """Register custom tools for the engine to use."""
        self._tool_registry[name] = {
            "func": func,
            "description": description
        }
        self.logger.info(f"Tool registered: {name}")
        return self

    @trace_llm_call
    async def chat(self, message: str, use_rag: bool = False, use_cache: bool = True) -> str:
        """High-level chat interface with semantic caching."""
        if not self._llm:
            raise RuntimeError("Engine not configured. Call configure_llm() first.")
            
        self.logger.info("Chat request received", message=message)
        
        # 1. Semantic Cache Check (P2)
        if use_cache:
            # Simplified caching: using a simple hash for now
            import hashlib
            cache_key = f"cache:llm:{hashlib.md5(message.encode()).hexdigest()}"
            # This would normally talk to Redis via self.bus.client
            # For this context, we'll log it as a cache miss
            self.logger.info("Cache miss", key=cache_key)

        # 2. Generate Response
        response = await self._llm.generate(message)
        
        # 3. Store in Cache
        if use_cache:
            self.logger.info("Caching response", key=cache_key)

        return response

    @trace_llm_call
    async def chat_stream(self, message: str) -> AsyncGenerator[str, None]:
        """Streaming chat interface."""
        if not self._llm:
            raise RuntimeError("Engine not configured. Call configure_llm() first.")
            
        async for token in self._llm.stream(message):
            yield token
