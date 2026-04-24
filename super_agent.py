from config_shared import OLLAMA_URL, DEFAULT_MODEL

class UltraLightAgent:
    """
    An Ultra-Lightweight Sovereign Agent running locally with < 2GB VRAM.
    Uses Ollama to query a small model (e.g., tinyllama or qwen2:0.5b).
    """
    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self.ollama_url = OLLAMA_URL
        self.memory = []
        self.tools = {
            "RAG_Anything": self._tool_rag_retrieve,
            "TrendRadar": self._tool_trend_analyze,
            "Stocksight": self._tool_stocksight_predict,
        }
        self.persona = "You are a local AI agent. You have tools: RAG_Anything, TrendRadar, Stocksight. Keep responses extremely short."

    def _query_ollama(self, prompt: str) -> str:
        try:
            response = requests.post(self.ollama_url, json={
                "model": self.model_name,
                "prompt": prompt,
                "stream": False
            }, timeout=10)
            if response.status_code == 200:
                return response.json().get("response", "")
            return "Error: Ollama model failed to respond."
        except requests.exceptions.RequestException:
            return "Ollama is not running. (Simulated Local Processing...)"

    def _tool_rag_retrieve(self, query: str) -> str:
        print(f"  [Tool] RAG-Anything retrieving: '{query}'")
        return f"Retrieved documents matching '{query}'"

    def _tool_trend_analyze(self, topic: str) -> str:
        print(f"  [Tool] TrendRadar analyzing: '{topic}'")
        return f"Trend analysis shows high engagement for '{topic}'"

    def _tool_stocksight_predict(self, ticker: str) -> str:
        print(f"  [Tool] Stocksight predicting for: '{ticker}'")
        return f"Stocksight predicts bullish movement for {ticker}."

    def run_task(self, task: str):
        print(f"\n{'='*50}\n[ULTRA LIGHT AGENT] Initialized with {self.model_name}.\n{'='*50}")
        print(f"[Task] -> {task}\n")

        # Step 1: Think (Ask local model what tool to use)
        prompt = f"{self.persona}\nTask: {task}\nWhat tool should I use first? Just reply with the tool name."
        print("[Agent is Thinking via Local LLM...]")
        llm_response = self._query_ollama(prompt)
        
        # Determine tool heuristically from small model response or fallback to logic
        action = None
        if "Stocksight" in llm_response or "stock" in task.lower():
            action = "Stocksight"
            arg = "NVDA"
        elif "TrendRadar" in llm_response or "trend" in task.lower():
            action = "TrendRadar"
            arg = "AI Frameworks"
        else:
            action = "RAG_Anything"
            arg = "General info"

        print(f"[LLM Decision] -> Using tool: {action}")
        
        # Step 2: Act
        result = self.tools[action](arg)
        self.memory.append({"action": action, "result": result})

        print("\n[OK] Task Complete. Memory summarized:")
        print(json.dumps(self.memory, indent=2))

if __name__ == "__main__":
    agent = UltraLightAgent(model_name="tinyllama")
    agent.run_task("Check the stock trends for NVDA.")
