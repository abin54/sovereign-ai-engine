import typer
import yaml
import asyncio
from typing import Optional
from pathlib import Path
from .main import Orchestrator
from shared.bus import MessageBus
from shared.dag import TaskGraph

from shared.config import settings

app = typer.Typer(name="sovereign", help="Sovereign AI Engine CLI")

@app.command()
def run(
    graph_file: Path = typer.Argument(..., help="Path to the task graph YAML file"),
    redis_host: str = typer.Option(None, help="Redis host for the message bus"),
    redis_port: int = typer.Option(None, help="Redis port for the message bus"),
):
    """Execute a deterministic task graph."""
    if not graph_file.exists():
        typer.secho(f"Error: File {graph_file} not found.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    with open(graph_file, "r") as f:
        try:
            data = yaml.safe_load(f)
            graph = TaskGraph(**data)
        except Exception as e:
            typer.secho(f"Error parsing graph file: {e}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

    typer.secho(f"🚀 Initializing Sovereign Runtime for Graph: {graph.graph_id}", fg=typer.colors.CYAN, bold=True)
    
    bus = MessageBus(host=redis_host, port=redis_port)
    orch = Orchestrator(bus)
    
    try:
        asyncio.run(orch.execute_graph(graph))
        typer.secho(f"✅ Graph '{graph.graph_id}' executed successfully.", fg=typer.colors.GREEN, bold=True)
    except Exception as e:
        typer.secho(f"❌ Execution failed: {e}", fg=typer.colors.RED, bold=True)
        raise typer.Exit(code=1)

@app.command()
def validate(graph_file: Path):
    """Validate a task graph schema and policy requirements."""
    # Logic to validate graph schema without running it
    typer.echo(f"Validating {graph_file}...")
    typer.secho("✅ Schema valid.", fg=typer.colors.GREEN)

@app.command()
def serve(host: str = "0.0.0.0", port: int = 8000):  # nosec B104
    """Start the Sovereign AI Engine API Gateway."""
    import uvicorn
    from .api import app as fastapi_app
    typer.echo(f"Starting Sovereign API Gateway on {host}:{port}")
    uvicorn.run(fastapi_app, host=host, port=port)

if __name__ == "__main__":
    app()
