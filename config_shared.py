import os

# LLM Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "tinyllama")

# Tool Paths
TREND_RADAR_PATH = "./TrendRadar"
STOCKSIGHT_PATH = "./stocksight"
RAG_ANYTHING_PATH = "./RAG-Anything"

# Memory Settings
CHROMA_DB_PATH = "./micro_dify_memory"
