FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the entire workspace
COPY . .

# Sync the workspace
RUN uv sync --frozen

# Default command (can be overridden)
CMD ["uv", "run", "python", "-m", "orchestrator.main"]
