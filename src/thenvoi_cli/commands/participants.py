"""Participant management commands."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from thenvoi_cli.config_manager import ConfigManager
from thenvoi_cli.exceptions import ConfigurationError
from thenvoi_cli.output import OutputFormat
from thenvoi_cli.sdk_client import SDKClient, run_async

app = typer.Typer(help="Manage room participants.")
console = Console()


@app.command("list")
def list_participants(
    room_id: str = typer.Argument(..., help="Room ID to list participants for."),
    agent_name: str = typer.Option(
        ...,
        "--agent",
        "-a",
        help="Agent to use for the request.",
    ),
    ctx: typer.Context = typer.Option(None),
) -> None:
    """List participants in a room.

    Example:
        thenvoi-cli participants list room-123 --agent my-agent
    """
    fmt = ctx.obj.get("format", OutputFormat.TABLE) if ctx.obj else OutputFormat.TABLE

    async def _list() -> list:
        config = ConfigManager()
        agent_id, api_key = config.load_agent(agent_name)
        client = SDKClient(agent_id=agent_id, api_key=api_key)

        await client.connect()
        try:
            tools = client.get_tools(room_id)
            return await tools.get_participants()
        finally:
            await client.disconnect()

    try:
        participants = run_async(_list())
    except ConfigurationError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    if not participants:
        if fmt == OutputFormat.JSON:
            console.print("[]")
        else:
            console.print("No participants in room")
        return

    if fmt == OutputFormat.JSON:
        import json

        console.print(json.dumps(participants, indent=2, default=str))
    elif fmt == OutputFormat.TABLE:
        table = Table(title=f"Participants in {room_id}")
        table.add_column("Name", style="cyan")
        table.add_column("Role")
        table.add_column("Type")

        for p in participants:
            table.add_row(
                p.get("name", "Unknown"),
                p.get("role", "member"),
                p.get("type", ""),
            )
        console.print(table)
    else:  # PLAIN
        for p in participants:
            console.print(f"{p.get('name', 'Unknown')} ({p.get('role', 'member')})")


@app.command("add")
def add_participant(
    room_id: str = typer.Argument(..., help="Room ID to add participant to."),
    name: str = typer.Argument(..., help="Name of the participant to add."),
    agent_name: str = typer.Option(
        ...,
        "--agent",
        "-a",
        help="Agent to use for the request.",
    ),
    role: str = typer.Option(
        "member",
        "--role",
        "-r",
        help="Role for the participant (member or admin).",
    ),
) -> None:
    """Add a participant to a room.

    Example:
        thenvoi-cli participants add room-123 "Research Bot" --agent my-agent
        thenvoi-cli participants add room-123 "Admin User" --agent my-agent --role admin
    """
    async def _add() -> dict:
        config = ConfigManager()
        agent_id, api_key = config.load_agent(agent_name)
        client = SDKClient(agent_id=agent_id, api_key=api_key)

        await client.connect()
        try:
            tools = client.get_tools(room_id)
            return await tools.add_participant(name, role=role)
        finally:
            await client.disconnect()

    try:
        result = run_async(_add())
        console.print(f"[green]Added[/green] '{name}' to room as {role}")
    except ConfigurationError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to add participant: {e}")
        raise typer.Exit(1)


@app.command("remove")
def remove_participant(
    room_id: str = typer.Argument(..., help="Room ID to remove participant from."),
    name: str = typer.Argument(..., help="Name of the participant to remove."),
    agent_name: str = typer.Option(
        ...,
        "--agent",
        "-a",
        help="Agent to use for the request.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Remove without confirmation.",
    ),
) -> None:
    """Remove a participant from a room.

    Example:
        thenvoi-cli participants remove room-123 "Research Bot" --agent my-agent
    """
    if not force:
        confirm = typer.confirm(f"Remove '{name}' from room {room_id}?", default=False)
        if not confirm:
            raise typer.Abort()

    async def _remove() -> dict:
        config = ConfigManager()
        agent_id, api_key = config.load_agent(agent_name)
        client = SDKClient(agent_id=agent_id, api_key=api_key)

        await client.connect()
        try:
            tools = client.get_tools(room_id)
            return await tools.remove_participant(name)
        finally:
            await client.disconnect()

    try:
        result = run_async(_remove())
        console.print(f"[green]Removed[/green] '{name}' from room")
    except ConfigurationError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to remove participant: {e}")
        raise typer.Exit(1)
