"""Status and stop commands."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from thenvoi_cli.output import OutputFormat
from thenvoi_cli.process_manager import process_manager

console = Console()


def status(
    agent_name: Optional[str] = typer.Argument(
        None,
        help="Specific agent to check, or all if not specified.",
    ),
    ctx: typer.Context = typer.Option(None),
) -> None:
    """Show status of running agents.

    Example:
        thenvoi-cli status
        thenvoi-cli status my-agent
        thenvoi-cli status --format json
    """
    fmt = ctx.obj.get("format", OutputFormat.TABLE) if ctx.obj else OutputFormat.TABLE

    if agent_name:
        # Show specific agent
        agent_status = process_manager.get_agent_status(agent_name)
        if agent_status:
            _display_single_status(agent_status, fmt)
        else:
            console.print(f"Agent '[cyan]{agent_name}[/cyan]' is [red]not running[/red]")
            raise typer.Exit(1)
    else:
        # Show all agents
        agents = process_manager.list_running_agents()
        if agents:
            _display_all_status(agents, fmt)
        else:
            if fmt == OutputFormat.JSON:
                console.print("[]")
            else:
                console.print("No agents running")
                console.print("[dim]Start one with: thenvoi-cli run <agent-name>[/dim]")


def _display_single_status(agent: object, fmt: OutputFormat) -> None:
    """Display status for a single agent."""
    from thenvoi_cli.process_manager import AgentProcess

    if not isinstance(agent, AgentProcess):
        return

    uptime = datetime.now() - agent.started_at
    uptime_str = _format_uptime(uptime.total_seconds())

    if fmt == OutputFormat.JSON:
        import json

        data = {
            "name": agent.name,
            "pid": agent.pid,
            "status": "running",
            "adapter": agent.adapter,
            "started_at": agent.started_at.isoformat(),
            "uptime_seconds": uptime.total_seconds(),
        }
        console.print(json.dumps(data, indent=2))
    elif fmt == OutputFormat.TABLE:
        console.print(f"[bold]Agent:[/bold] {agent.name}")
        console.print(f"[bold]Status:[/bold] [green]running[/green]")
        console.print(f"[bold]PID:[/bold] {agent.pid}")
        console.print(f"[bold]Adapter:[/bold] {agent.adapter or 'unknown'}")
        console.print(f"[bold]Started:[/bold] {agent.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
        console.print(f"[bold]Uptime:[/bold] {uptime_str}")
    else:  # PLAIN
        console.print(f"{agent.name}: running (PID {agent.pid}, uptime {uptime_str})")


def _display_all_status(agents: list, fmt: OutputFormat) -> None:
    """Display status for all agents."""
    from thenvoi_cli.process_manager import AgentProcess

    if fmt == OutputFormat.JSON:
        import json

        data = []
        for agent in agents:
            if isinstance(agent, AgentProcess):
                uptime = datetime.now() - agent.started_at
                data.append({
                    "name": agent.name,
                    "pid": agent.pid,
                    "status": "running",
                    "adapter": agent.adapter,
                    "started_at": agent.started_at.isoformat(),
                    "uptime_seconds": uptime.total_seconds(),
                })
        console.print(json.dumps(data, indent=2))
    elif fmt == OutputFormat.TABLE:
        table = Table(title="Running Agents")
        table.add_column("Name", style="cyan")
        table.add_column("Status")
        table.add_column("PID")
        table.add_column("Adapter")
        table.add_column("Uptime")

        for agent in agents:
            if isinstance(agent, AgentProcess):
                uptime = datetime.now() - agent.started_at
                table.add_row(
                    agent.name,
                    "[green]running[/green]",
                    str(agent.pid),
                    agent.adapter or "unknown",
                    _format_uptime(uptime.total_seconds()),
                )
        console.print(table)
    else:  # PLAIN
        for agent in agents:
            if isinstance(agent, AgentProcess):
                uptime = datetime.now() - agent.started_at
                console.print(
                    f"{agent.name}: running (PID {agent.pid}, uptime {_format_uptime(uptime.total_seconds())})"
                )


def _format_uptime(seconds: float) -> str:
    """Format uptime in human-readable form."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
    else:
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        return f"{days}d {hours}h"


def stop(
    agent_name: Optional[str] = typer.Argument(
        None,
        help="Agent to stop, or all if --all is used.",
    ),
    all_agents: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Stop all running agents.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force stop (SIGKILL instead of SIGTERM).",
    ),
    timeout: int = typer.Option(
        30,
        "--timeout",
        "-t",
        help="Seconds to wait before force killing.",
    ),
) -> None:
    """Stop a running agent.

    Example:
        thenvoi-cli stop my-agent
        thenvoi-cli stop --all
        thenvoi-cli stop my-agent --force
    """
    if all_agents:
        count = process_manager.stop_all(force=force)
        if count > 0:
            console.print(f"[green]Stopped[/green] {count} agent(s)")
        else:
            console.print("No agents were running")
        return

    if not agent_name:
        console.print("[red]Error:[/red] Specify an agent name or use --all")
        raise typer.Exit(1)

    if not process_manager.is_running(agent_name):
        console.print(f"Agent '[cyan]{agent_name}[/cyan]' is not running")
        raise typer.Exit(1)

    action = "Force stopping" if force else "Stopping"
    console.print(f"{action} agent '[cyan]{agent_name}[/cyan]'...")

    if process_manager.stop_agent(agent_name, force=force, timeout=timeout):
        console.print(f"[green]Stopped[/green] agent '{agent_name}'")
    else:
        console.print(f"[red]Failed[/red] to stop agent '{agent_name}'")
        raise typer.Exit(1)
