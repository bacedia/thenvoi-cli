"""Run command for starting agents."""

from __future__ import annotations

import asyncio
import os
import signal
import sys
from typing import Optional

import typer
from rich.console import Console

from thenvoi_cli.adapter_registry import registry
from thenvoi_cli.config_manager import ConfigManager
from thenvoi_cli.exceptions import (
    AdapterError,
    ConfigurationError,
    ConnectionError,
    MissingDependencyError,
    MissingEnvironmentError,
)
from thenvoi_cli.logging_config import get_logger
from thenvoi_cli.process_manager import process_manager

console = Console()


def run(
    agent_name: str = typer.Argument(..., help="Agent name from configuration."),
    adapter: str = typer.Option(
        "langgraph",
        "--adapter",
        "-a",
        help="Adapter to use (langgraph, anthropic, claude-sdk, etc.).",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Model to use (overrides adapter default).",
    ),
    background: bool = typer.Option(
        False,
        "--background",
        "-b",
        help="Run in background (daemonize).",
    ),
    timeout: int = typer.Option(
        30,
        "--timeout",
        "-t",
        help="Shutdown timeout in seconds.",
    ),
    ws_url: Optional[str] = typer.Option(
        None,
        "--ws-url",
        help="Override WebSocket URL.",
    ),
    rest_url: Optional[str] = typer.Option(
        None,
        "--rest-url",
        help="Override REST API URL.",
    ),
    ctx: typer.Context = typer.Option(None),
) -> None:
    """Run an agent connected to the Thenvoi platform.

    Example:
        thenvoi-cli run my-agent
        thenvoi-cli run my-agent --adapter anthropic --model claude-sonnet-4-5-20250929
        thenvoi-cli run my-agent --background
    """
    logger = get_logger()

    # Load configuration
    config = ConfigManager()
    try:
        agent_id, api_key = config.load_agent(agent_name)
    except ConfigurationError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        if e.hint:
            console.print(f"[yellow]Hint:[/yellow] {e.hint}")
        raise typer.Exit(1)

    # Validate URLs
    effective_ws_url = ws_url or os.getenv("THENVOI_WS_URL")
    effective_rest_url = rest_url or os.getenv("THENVOI_REST_URL")

    if not effective_ws_url:
        console.print("[red]Error:[/red] THENVOI_WS_URL not set")
        console.print("[yellow]Hint:[/yellow] export THENVOI_WS_URL=wss://app.thenvoi.com/...")
        raise typer.Exit(1)

    if not effective_rest_url:
        console.print("[red]Error:[/red] THENVOI_REST_URL not set")
        console.print("[yellow]Hint:[/yellow] export THENVOI_REST_URL=https://app.thenvoi.com/")
        raise typer.Exit(1)

    # Check adapter availability
    if not registry.get_adapter_info(adapter):
        available = ", ".join(registry.list_adapters())
        console.print(f"[red]Error:[/red] Unknown adapter '{adapter}'")
        console.print(f"Available adapters: {available}")
        raise typer.Exit(1)

    if not registry.is_available(adapter):
        missing = registry.get_missing_deps(adapter)
        console.print(f"[red]Error:[/red] Adapter '{adapter}' has missing dependencies: {', '.join(missing)}")
        console.print(f"[yellow]Hint:[/yellow] pip install thenvoi-cli[{adapter}]")
        raise typer.Exit(1)

    # Check required environment variables for adapter
    required_env = registry.get_required_env_vars(adapter)
    for var in required_env:
        if not os.getenv(var):
            console.print(f"[red]Error:[/red] Required environment variable '{var}' not set for {adapter} adapter")
            raise typer.Exit(1)

    # Get effective model
    effective_model = model or registry.get_default_model(adapter)

    # Check if already running
    if process_manager.is_running(agent_name):
        console.print(f"[yellow]Warning:[/yellow] Agent '{agent_name}' is already running")
        console.print("Use 'thenvoi-cli stop' to stop it first")
        raise typer.Exit(1)

    if background:
        # Fork and daemonize
        _run_background(
            agent_name=agent_name,
            agent_id=agent_id,
            api_key=api_key,
            adapter=adapter,
            model=effective_model,
            ws_url=effective_ws_url,
            rest_url=effective_rest_url,
            timeout=timeout,
        )
    else:
        # Run in foreground
        _run_foreground(
            agent_name=agent_name,
            agent_id=agent_id,
            api_key=api_key,
            adapter=adapter,
            model=effective_model,
            ws_url=effective_ws_url,
            rest_url=effective_rest_url,
            timeout=timeout,
        )


def _run_foreground(
    agent_name: str,
    agent_id: str,
    api_key: str,
    adapter: str,
    model: str | None,
    ws_url: str,
    rest_url: str,
    timeout: int,
) -> None:
    """Run agent in foreground."""
    logger = get_logger()

    console.print(f"Starting agent '[cyan]{agent_name}[/cyan]' with {adapter} adapter...")
    if model:
        console.print(f"Model: {model}")
    console.print(f"Press Ctrl+C to stop\n")

    async def _run() -> None:
        try:
            from thenvoi import Agent

            # Get adapter class and instantiate
            adapter_class = registry.get_adapter_class(adapter)
            adapter_instance = _create_adapter_instance(adapter_class, adapter, model)

            # Create agent
            agent = Agent.create(
                adapter=adapter_instance,
                agent_id=agent_id,
                api_key=api_key,
                ws_url=ws_url,
                rest_url=rest_url,
            )

            # Register for cleanup
            process_manager.register_agent(agent_name, os.getpid(), adapter)

            # Set up signal handlers
            loop = asyncio.get_event_loop()

            def signal_handler() -> None:
                console.print("\n[yellow]Shutting down...[/yellow]")
                asyncio.create_task(agent.stop(timeout=timeout))

            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, signal_handler)

            # Run the agent
            console.print("[green]Connected[/green] to Thenvoi platform")
            await agent.run()

        except Exception as e:
            logger.exception("Agent error")
            console.print(f"[red]Error:[/red] {e}")
            raise
        finally:
            process_manager.unregister_agent(agent_name)

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
    finally:
        console.print(f"Agent '{agent_name}' stopped")


def _run_background(
    agent_name: str,
    agent_id: str,
    api_key: str,
    adapter: str,
    model: str | None,
    ws_url: str,
    rest_url: str,
    timeout: int,
) -> None:
    """Run agent in background (daemonize)."""
    # Fork
    pid = os.fork()
    if pid > 0:
        # Parent process
        console.print(f"Started agent '[cyan]{agent_name}[/cyan]' in background (PID: {pid})")
        console.print(f"Use 'thenvoi-cli status' to check status")
        console.print(f"Use 'thenvoi-cli stop {agent_name}' to stop")
        return

    # Child process - daemonize
    os.setsid()

    # Fork again
    pid = os.fork()
    if pid > 0:
        os._exit(0)

    # Redirect standard file descriptors
    sys.stdin.close()
    sys.stdout.close()
    sys.stderr.close()

    # Now run the agent
    _run_foreground(
        agent_name=agent_name,
        agent_id=agent_id,
        api_key=api_key,
        adapter=adapter,
        model=model,
        ws_url=ws_url,
        rest_url=rest_url,
        timeout=timeout,
    )
    os._exit(0)


def _create_adapter_instance(
    adapter_class: type,
    adapter_name: str,
    model: str | None,
) -> object:
    """Create an adapter instance with appropriate configuration."""
    # This is a simplified version - real implementation would be more sophisticated
    if adapter_name == "langgraph":
        from langchain_openai import ChatOpenAI
        from langgraph.checkpoint.memory import InMemorySaver

        llm = ChatOpenAI(model=model or "gpt-4o")
        return adapter_class(llm=llm, checkpointer=InMemorySaver())

    elif adapter_name == "anthropic":
        return adapter_class(model=model or "claude-sonnet-4-5-20250929")

    elif adapter_name == "claude-sdk":
        return adapter_class(model=model or "claude-sonnet-4-5-20250929")

    elif adapter_name == "pydantic-ai":
        return adapter_class(model=model or "openai:gpt-4o")

    elif adapter_name == "crewai":
        return adapter_class(
            model=model or "gpt-4o",
            role="AI Assistant",
            goal="Help users with their tasks",
            backstory="An intelligent AI assistant",
        )

    elif adapter_name == "parlant":
        return adapter_class(model=model or "gpt-4o")

    elif adapter_name == "a2a":
        # A2A needs a URL
        a2a_url = os.getenv("A2A_AGENT_URL")
        if not a2a_url:
            raise MissingEnvironmentError("A2A_AGENT_URL")
        return adapter_class(a2a_url=a2a_url)

    elif adapter_name == "a2a-gateway":
        return adapter_class()

    else:
        # Default: try to instantiate with model
        try:
            return adapter_class(model=model)
        except TypeError:
            return adapter_class()
