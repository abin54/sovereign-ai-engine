import httpx
import json
from typing import Any, Dict, List, Optional, AsyncGenerator

class SovereignClient:
    """The official Python SDK for the Sovereign AI Engine."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }

    async def chat(self, message: str, conversation_id: Optional[str] = None, use_rag: bool = False, **kwargs) -> Dict[str, Any]:
        """Send a chat request to the engine."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "message": message,
                "conversation_id": conversation_id,
                "use_rag": use_rag,
                **kwargs
            }
            resp = await client.post(f"{self.base_url}/v1/chat", json=payload, headers=self.headers)
            resp.raise_for_status()
            return resp.json()

    async def chat_stream(self, message: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream a chat response from the engine."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {"message": message, **kwargs}
            async with client.stream("POST", f"{self.base_url}/v1/chat/stream", json=payload, headers=self.headers) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        token = line[6:]
                        if token == "[DONE]":
                            break
                        yield token

    async def ingest_document(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Upload and ingest a document for RAG."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            # We don't send Content-Type: application/json here as httpx handles multipart
            headers = self.headers.copy()
            del headers["Content-Type"]
            
            with open(file_path, "rb") as f:
                files = {"file": (file_path, f)}
                data = {"metadata": json.dumps(metadata)} if metadata else {}
                resp = await client.post(
                    f"{self.base_url}/v1/documents/ingest", 
                    files=files, 
                    data=data,
                    headers=headers
                )
                resp.raise_for_status()
                return resp.json()

    async def get_stats(self) -> Dict[str, Any]:
        """Fetch admin statistics."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/admin/stats", headers=self.headers)
            resp.raise_for_status()
            return resp.json()
