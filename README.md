# Sovereign AI Engine 🛡️

The first AI framework built for high-stakes environments where **reproducibility**, **policy enforcement**, and **zero-trust execution** are non-negotiable.

Sovereign transforms LLMs from unpredictable black boxes into deterministic, secure components of your enterprise stack.

## 🚀 Quick Start (True Sovereignty Mode)

### 1. Deploy the Infrastructure
```bash
git clone https://github.com/abin54/sovereign-ai-engine.git
cd sovereign-ai-engine
cp .env.example .env
# Edit .env with your config
```

### 2. Start Ollama (The actual sovereign backend)
```bash
docker run -d --gpus all -v ollama_data:/root/.ollama -p 11434:11434 ollama/ollama
docker exec ollama ollama pull llama3
docker exec ollama ollama pull nomic-embed-text
```

### 3. Start the Sovereign Stack
```bash
docker compose -f docker-compose.prod.yml up -d
```

### 4. Ingest Private Knowledge
```bash
curl -X POST http://localhost:80/v1/documents/ingest \
  -H "X-API-Key: sk-sovereign-admin-xxxxx" \
  -F "file=@company_handbook.pdf"
```

### 5. Secure Query with RAG
```bash
curl -X POST http://localhost:80/v1/chat \
  -H "X-API-Key: sk-sovereign-admin-xxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is our remote work policy?",
    "use_rag": true
  }'
```

## 🏗️ Architecture: The Zero-Trust Engine
Unlike "convenience-first" wrappers, Sovereign is built on four pillars of integrity:

1. **Deterministic DAG Execution**: Every AI workflow is a structured graph. No autonomous hallucinations, no infinite loops.
2. **Kernel-Level Sandboxing (nsjail)**: Tools and agents run in isolated environments with zero access to your host filesystem or network unless explicitly granted.
3. **Immutable Audit Ledger**: Every action, tool call, and AI response is hash-chained and HMAC-signed. Your compliance team can verify the integrity of the engine's history offline.
4. **Multi-LLM Agnostic**: Hot-swap between **OpenAI**, **Anthropic**, **vLLM**, or **Llama.cpp** without changing a line of code.

## 📊 Sovereignty Scorecard

| Feature | Sovereign AI Engine | Standard Wrapper |
| :--- | :---: | :---: |
| **Execution Model** | Deterministic DAG | Autonomous Loop |
| **Sandboxing** | nsjail / gVisor | subprocess.run |
| **Audit Log** | Hash-chained & Signed | Plain SQLite |
| **Local LLM** | Native (Ollama/vLLM) | Cloud-Only |
| **Infrastructure** | Microservices + K8s | Monolithic Script |

## 🛡️ Security Posture
Sovereign operates on a **Default-Deny** basis. Capabilities must be explicitly granted to tasks:
- `FS_READ`: Access specific directories.
- `NET_OUTBOUND`: Access specific host/port pairs.
- `SHELL_EXEC`: Run strictly validated commands.

## 🤝 Contributing
We welcome contributions that prioritize security over convenience. See [CONTRIBUTING.md](./CONTRIBUTING.md) for our engineering standards.

---
**Honest Disclaimer**: Sovereign is a high-integrity runtime. If you are looking for a "one-click" autonomous agent to browse the web for you, this is not it. If you are looking to deploy AI in a regulated, secure, or air-gapped environment, you are in the right place.
