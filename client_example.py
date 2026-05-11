import asyncio
from shared.client import SovereignClient

# Usage Example: Sovereign Support Bot
async def run_support_bot():
    client = SovereignClient(
        base_url="http://localhost:80",
        api_key="sk-sovereign-admin" # Ensure this matches your .env
    )

    print("--- Sovereign Support Bot ---")
    
    # 1. Ingest Knowledge (RAG)
    print("Ingesting knowledge documents...")
    # These files should exist in your local directory for the example to work
    # await client.ingest_document("faq.pdf")
    # await client.ingest_document("troubleshooting.md")
    
    # 2. Query with Grounded Reasoning
    print("Querying engine...")
    response = await client.chat(
        "How do I configure the zero-trust sandboxing?",
        use_rag=True,
        temperature=0.3
    )
    
    print("\n[Engine Response]:")
    print(response.get("response"))
    
    # 3. Check Stats
    print("\nFetching system stats...")
    stats = await client.get_stats()
    print(f"Total Requests Processed: {stats.get('total_requests')}")

if __name__ == "__main__":
    try:
        asyncio.run(run_support_bot())
    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: Ensure the Sovereign Engine stack is running (docker-compose up).")
