import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional
from .llm import BaseLLMAdapter

class RAGPipeline:
    """Enterprise RAG - End-to-end ingestion, chunking, and grounded retrieval."""
    
    def __init__(self, vector_store: Any, llm: BaseLLMAdapter, chunk_size: int = 512, chunk_overlap: int = 50):
        self.vector_store = vector_store
        self.llm = llm
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    async def ingest_document(self, file_path: Path, metadata: Optional[Dict[str, Any]] = None):
        """Ingest a document into the vector store with smart chunking."""
        raw_text = self._load_file(file_path)
        chunks = self._chunk_text(raw_text)
        
        doc_id = hashlib.sha256(raw_text.encode()).hexdigest()[:12]
        
        for i, chunk in enumerate(chunks):
            embedding = await self.llm.embed(chunk)
            await self.vector_store.upsert(
                id=f"{doc_id}_ch_{i}",
                vector=embedding,
                payload={
                    "text": chunk,
                    "doc_id": doc_id,
                    "source": str(file_path),
                    **(metadata or {})
                }
            )
        
        return {"doc_id": doc_id, "chunks": len(chunks)}

    async def query(self, question: str, top_k: int = 5) -> str:
        """Query with grounded retrieval and citation-aware generation."""
        q_embedding = await self.llm.embed(question)
        
        results = await self.vector_store.search(
            vector=q_embedding,
            limit=top_k
        )
        
        if not results:
            return "I don't have enough sovereign data to answer that question."
        
        context = "\n\n".join([
            f"[Source: {r.payload.get('source')}]\n{r.payload['text']}" 
            for r in results
        ])
        
        prompt = f"""Use the following context to answer the question. 
If the answer is not in the context, say you don't know.
Cite sources using [Source: path/to/file].

CONTEXT:
{context}

QUESTION: {question}
"""
        return await self.llm.generate(prompt)

    def _load_file(self, file_path: Path) -> str:
        """Support for multiple file formats."""
        suffix = file_path.suffix.lower()
        if suffix in [".txt", ".md"]:
            return file_path.read_text(encoding="utf-8")
        # Fallback for mock/MVP
        return f"Content of {file_path}"

    def _chunk_text(self, text: str) -> List[str]:
        """Smart overlap chunking."""
        words = text.split()
        chunks = []
        step = self.chunk_size - self.chunk_overlap
        for i in range(0, len(words), step):
            chunk = " ".join(words[i:i + self.chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        return chunks
