import asyncio
from shared.client import SovereignClient

async def run_support_bot():
    """
    Example: Sovereign Support Bot with RAG
    Combines local LLMs with private knowledge documents.
    """
    client = SovereignClient(
        base_url="http://localhost:80",
        api_key="sk-sovereign-admin"
    )

    print("--- Sovereign Support Bot ---")
    
    # 1. Ingest Private Docs (Normally these would be your PDF/MD files)
    print("Ingesting internal knowledge...")
    # await client.ingest_document("docs/policy_v1.pdf")
    
    # 2. Query with Grounding
    question = "What is the procedure for zero-trust sandbox allocation?"
    print(f"Question: {question}")

    response = await client.chat(
        question,
        use_rag=True,
        model="llama3", # Local Ollama
        temperature=0.3
    )
    
    print("\n[Grounded Response]:")
    print(response.get("response"))

if __name__ == "__main__":
    asyncio.run(run_support_bot())
