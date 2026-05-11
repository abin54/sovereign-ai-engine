# Sovereign AI Engine: The Deterministic AI Runtime

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/abin54/sovereign-ai-engine)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **"Reproduction is the soul of reliability."**
> Sovereign is the first AI framework built for high-stakes environments where reproducibility, policy enforcement, and zero-trust execution are non-negotiable.

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/abin54/sovereign-ai-engine.git
cd sovereign-ai-engine

# Initialize the workspace using uv
uv sync
```

### Running a Deterministic Task

```bash
# Execute a task graph with full audit logging and policy enforcement
sovereign run ./examples/security_scan.yaml
```

---

## 🏗️ Architecture

Sovereign replaces "broadcast-and-hope" agent loops with a **Deterministic Task Graph (DTG)**.

- **Task Nodes**: Pydantic-validated nodes with strict input/output schemas.
- **Capability-Based Security**: Tools execute in a gVisor-inspired sandbox with granular permissions.
- **Immutable Ledger**: Every action is recorded in a tamper-resistant SQLite audit ledger.
- **Async Messaging**: Microservice architecture powered by Redis Streams.

---

## ⚖️ Comparison

| Feature | General Agent Frameworks | Sovereign AI Engine |
| :--- | :--- | :--- |
| **Execution Model** | Autonomous Loops (Probabilistic) | Deterministic Task Graphs (DAG) |
| **Security Model** | Managed Cloud / Permission-based | Capability-Based (Default-Deny) |
| **Validation** | Runtime Assertions | Type-Safe Pydantic Models |
| **Audit Trail** | External Observability Tools | Local Hash-Chained Audit Ledger |
| **Isolation** | Container-Level | Granular Tool-Level Sandboxing |

---

## 🎯 When to Use Sovereign (and When NOT To)

Sovereign is a **local-first, minimal-footprint runtime**. It is not a replacement for enterprise-grade distributed systems.

### Use Sovereign IF

- You need a **single-binary-feel** runtime that runs entirely on local/air-gapped hardware.
- You require **embedded audit logs** (SQLite) without a SaaS dependency.
- You are building a **lightweight CLI tool** or edge-device agent.

### Use [Best-of-Breed] Tools IF

- **Orchestration**: You need complex scheduling and retries at scale → Use **Prefect** or **Dagster**.
- **Agent Logic**: You need a mature, community-backed graph framework → Use **LangGraph**.
- **Sandboxing**: You need production-grade microVM isolation *today* → Use **E2B**.
- **Observability**: You need an interactive, team-based dashboard → Use **Langfuse**.
- **Production Agents**: You need a battle-tested framework with multi-agent support → Use **CrewAI** or **AutoGen**.

---

## 🛡️ Security & Zero-Trust

The Sovereign runtime enforces a **Default-DENY** policy. No tool can access the filesystem, network, or shell without an explicit capability grant.

- **Isolation**: Tools run in temporary, isolated directories.
- **Integrity**: Audit logs are stored in a SQLite database with Write-Ahead Logging (WAL).
- **Control**: Subprocess execution avoids `shell=True` to prevent command injection.

---

## 🗺️ Roadmap

### 30-Day: Foundation

- [x] Monorepo Transition
- [x] Zero-Trust Executor MVP
- [ ] Comprehensive CLI (`sovereign-cli`)
- [ ] Task Graph Schema Validation

### 90-Day: Scale

- [x] Docker-based MicroVM Sandboxing (Initial Docker Support)
- [x] Distributed Task Execution (Redis Streams)
- [ ] Real-time Observability Dashboard

### 180-Day: Ecosystem

- [ ] Sovereign Hub (Shared Task Graphs)
- [ ] Long-term Cognitive Memory Service
- [ ] Local-first LLM Optimization

---

## 🐳 Running with Docker

The easiest way to run the full Sovereign stack (Redis, Orchestrator, and Skills) is via Docker Compose:

```bash
docker-compose up --build
```

This will start:

- **Redis**: The message broker.
- **Orchestrator**: The DAG execution engine.
- **Skills (Security, ML, Memory)**: Worker services that process tasks.

### Submitting a Task

Once the services are running, you can submit a task graph using the CLI:

```bash
uv run sovereign run ./examples/security_scan.yaml
```

---

## 🤝 Contributing

We welcome contributions from engineers who value reliability over hype. Please read our [Contributing Guide](CONTRIBUTING.md) to get started.

---

## 📄 License

MIT © Abinash Sahu
