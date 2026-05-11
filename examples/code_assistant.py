import asyncio
from shared.client import SovereignClient

async def code_security_review():
    """
    Example: Local Code Security Assistant
    Your code NEVER leaves your machine. Processing happens 100% locally on Ollama.
    """
    client = SovereignClient(
        base_url="http://localhost:80",
        api_key="sk-sovereign-admin"
    )

    code_snippet = """
    def get_user_data(user_id):
        query = f"SELECT * FROM users WHERE id = {user_id}"
        cursor.execute(query)
        return cursor.fetchone()
    """

    print("--- Local Code Security Review ---")
    print("Analyzing code snippet locally...")

    response = await client.chat(
        f"Review this code for security issues and suggest a fix:\n\n```python\n{code_snippet}\n```",
        model="codellama", # Runs locally via Ollama
        temperature=0.1
    )

    print("\n[Local Analysis]:")
    print(response.get("response"))

if __name__ == "__main__":
    asyncio.run(code_security_review())
