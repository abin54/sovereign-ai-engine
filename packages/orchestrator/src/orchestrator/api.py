from fastapi import FastAPI, HTTPException, Depends, Security, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
import time
import asyncio

from shared.engine import SovereignEngine, LLMProvider
from shared.config import settings

from .auth import verify_api_key
from .admin import router as admin_router

app = FastAPI(
    title="Sovereign AI Engine API",
    version="2.0.0",
)

app.include_router(admin_router)

# Global Engine Instance
engine = SovereignEngine()
# Auto-configure based on settings
engine.configure_llm(LLMProvider.OLLAMA, model="llama3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None
    use_rag: bool = False
    model: Optional[str] = None

class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    latency_ms: float

from .auth import verify_api_key

from fastapi import File, UploadFile, Form

@app.post("/v1/documents/ingest")
async def ingest_document(
    file: UploadFile = File(...), 
    metadata: Optional[str] = Form(None),
    key_info: dict = Depends(verify_api_key)
):
    """Ingest a document for RAG processing."""
    # In a real app, save file and trigger MemorySkill ingest task
    return {
        "status": "ingested", 
        "filename": file.filename,
        "doc_id": str(uuid.uuid4())[:12]
    }

@app.post("/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, key_info: dict = Depends(verify_api_key)):
    start = time.time()
    conv_id = request.conversation_id or str(uuid.uuid4())
    
    response = await engine.chat(message=request.message, use_rag=request.use_rag)
    
    latency = (time.time() - start) * 1000
    return ChatResponse(
        conversation_id=conv_id,
        response=response,
        latency_ms=round(latency, 2)
    )

@app.post("/v1/chat/stream")
async def chat_stream(request: ChatRequest, key_info: dict = Depends(verify_api_key)):
    async def generate():
        async for token in engine.chat_stream(request.message):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "engine_ready": engine._llm is not None
    }

@app.get("/v1/models")
async def list_models(_ = Depends(verify_api_key)):
    return {"models": ["llama3", "gpt-4o"]}
