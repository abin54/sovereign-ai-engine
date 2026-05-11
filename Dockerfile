# Stage 1: Builder
FROM ghcr.io/astral-sh/uv:latest AS builder
WORKDIR /app
COPY . .
RUN uv sync --frozen

# Stage 2: Runtime
FROM python:3.12-slim AS runtime
WORKDIR /app

# SECURITY: Create non-root user and install minimal dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && groupadd -r sovereign && useradd -r -g sovereign sovereign \
    && rm -rf /var/lib/apt/lists/*

# Copy synced workspace from builder
COPY --from=builder /app /app
COPY --chown=sovereign:sovereign . .

# Update PATH to include uv-installed binaries
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# HEALTHCHECK
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Switch to non-root
USER sovereign

# Default entry point
CMD ["python", "-m", "orchestrator.main"]
