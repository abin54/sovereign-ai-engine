# Contributing to Sovereign AI Engine

We welcome contributions from engineers who value reliability, determinism, and security over hype.

## 🛠️ Development Setup

1. **Prerequisites**:
   - Python 3.10+
   - [uv](https://github.com/astral-sh/uv) package manager
   - Node.js and [pnpm](https://pnpm.io/) (for web UI)
   - Redis server (running on `localhost:6379`)

2. **Clone and Install**:
   ```bash
   git clone https://github.com/abin54/sovereign-ai-engine.git
   cd sovereign-ai-engine
   uv sync
   pnpm install
   ```

3. **Running Tests**:
   ```bash
   # Run all python tests
   pytest
   ```

## 📜 Development Guidelines

- **Pydantic Everywhere**: Use Pydantic models for all data structures and API contracts.
- **Deterministic by Design**: Avoid non-deterministic loops or uncontrolled side effects.
- **Security First**: Every new tool must have a defined capability and follow the default-deny policy.
- **Monorepo Structure**: Keep logic within appropriate packages:
  - `packages/shared`: Shared models, security interfaces, and messaging bus.
  - `packages/orchestrator`: The core DAG execution engine.
  - `packages/skills-*`: Domain-specific tool implementations.

## 🤝 Pull Request Process

1. Create a feature branch from `main`.
2. Ensure all tests pass.
3. Update documentation if necessary.
4. Submit the PR with a clear description of the changes and the problem being solved.

## 🛡️ Security
If you find a security vulnerability, please report it via GitHub Issues using the "Security" label or contact the maintainers directly.
