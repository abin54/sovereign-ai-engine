import sys
import os

# Set up paths
cwd = os.getcwd()
sys.path.append(cwd)
sys.path.append(os.path.join(cwd, "stocksight"))
sys.path.append(os.path.join(cwd, "TrendRadar"))

print("--- Testing Integrated AI Assistant Modules ---")

# 1. Test Stocksight Integration
try:
    from sentiment import sentiment_analysis
    polarity, subjectivity, sentiment = sentiment_analysis("This project is looking amazing and very stable!")
    print(f"[OK] Stocksight Sentiment: {sentiment.upper()} (Polarity: {polarity:.2f})")
except Exception as e:
    print(f"[FAIL] Stocksight: {e}")

# 2. Test TrendRadar Integration
try:
    from trendradar.crawler import DataFetcher
    fetcher = DataFetcher()
    # Note: We won't actually perform a network request here to avoid lag/errors, 
    # but we'll check if the class initializes.
    print(f"[OK] TrendRadar DataFetcher: Initialized successfully.")
except Exception as e:
    print(f"[FAIL] TrendRadar: {e}")

# 3. Test Config
try:
    from config_shared import DEFAULT_MODEL, OLLAMA_URL
    print(f"[OK] Config Loaded: Model={DEFAULT_MODEL}, URL={OLLAMA_URL}")
except Exception as e:
    print(f"[FAIL] Config: {e}")

print("--- Verification Complete ---")
