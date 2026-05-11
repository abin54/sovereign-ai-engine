import asyncio
from shared.engine import SovereignEngine, Agent, LLMProvider

class ResearchWorkflow:
    """A deterministic, multi-agent research and review pipeline."""
    
    def __init__(self, engine: SovereignEngine):
        self.engine = engine
        self.researcher = Agent(engine, system_prompt="You are a meticulous research analyst.")
        self.writer = Agent(engine, system_prompt="You are a professional technical writer.")
        self.reviewer = Agent(engine, system_prompt="You are a critical quality assurance reviewer.")
    
    async def run(self, topic: str) -> str:
        print(f"--- Starting Research Workflow for: {topic} ---")
        
        # Step 1: Research Phase
        print("[1/4] Researching...")
        research = await self.researcher.run(f"Conduct deep research on: {topic}")
        
        # Step 2: Drafting Phase
        print("[2/4] Drafting article...")
        draft = await self.writer.run(f"Write a comprehensive article based on this research:\n{research}")
        
        # Step 3: Review Phase
        print("[3/4] Reviewing quality...")
        review = await self.reviewer.run(f"Critique this article for accuracy and clarity:\n{draft}")
        
        # Step 4: Final Polishing
        print("[4/4] Polishing final version...")
        final = await self.writer.run(
            f"Apply these improvements to the original draft:\n\nDRAFT:\n{draft}\n\nIMPROVEMENTS:\n{review}"
        )
        
        print("--- Workflow Complete ---")
        return final

async def main():
    # Initialize Engine
    engine = SovereignEngine()
    engine.configure_llm(LLMProvider.OLLAMA, model="llama3")

    workflow = ResearchWorkflow(engine)
    result = await workflow.run("The impact of bare-metal AI on data sovereignty")
    
    print("\n[Final Output]:")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
