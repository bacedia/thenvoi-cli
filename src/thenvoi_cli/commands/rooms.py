"""Room management commands."""

from __future__ import annotations

import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from thenvoi_cli.config_manager import ConfigManager
from thenvoi_cli.exceptions import ConfigurationError, ConnectionError
from thenvoi_cli.output import OutputFormat
from thenvoi_cli.sdk_client import SDKClient, run_async

app = typer.Typer(help="Manage chat rooms.")
console = Console()


@app.command("list")
def list_rooms(
    agent_name: str = typer.Option(
        ...,
        "--agent",
        "-a",
        help="Agent to use for the request.",
    ),
    ctx: typer.Context = typer.Option(None),
) -> None:
    """List rooms the agent has access to.

    Example:
        thenvoi-cli rooms list --agent my-agent
        thenvoi-cli rooms list --agent my-agent --format json
    """
    fmt = ctx.obj.get("format", OutputFormat.TABLE) if ctx.obj else OutputFormat.TABLE

    async def _list() -> list:
        config = ConfigManager()
        agent_id, api_key = config.load_agent(agent_name)
        client = SDKClient(agent_id=agent_id, api_key=api_key)

        await client.connect()
        try:
            return await client.get_rooms()
        finally:
            await client.disconnect()

    try:
        rooms = run_async(_list())
    except ConfigurationError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)
    except ConnectionError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    if not rooms:
        if fmt == OutputFormat.JSON:
            console.print("[]")
        else:
            console.print("No rooms found")
        return

    if fmt == OutputFormat.JSON:
        import json

        console.print(json.dumps(rooms, indent=2, default=str))
    elif fmt == OutputFormat.TABLE:
        table = Table(title="Rooms")
        table.add_column("ID", style="cyan")
        table.add_column("Name")
        table.add_column("Participants")

        for room in rooms:
            table.add_row(
                str(room.get("id", "")),
                room.get("name", ""),
                str(room.get("participant_count", len(room.get("participants", [])))),
            )
        console.print(table)
    else:  # PLAIN
        for room in rooms:
            console.print(f"{room.get('id', '')}: {room.get('name', '')}")


@app.command("send")
def send_message(
    room_id: str = typer.Argument(..., help="Room ID to send message to."),
    message: str = typer.Argument(
        ...,
        help="Message to send. Use '-' to read from stdin.",
    ),
    agent_name: str = typer.Option(
        ...,
        "--agent",
        "-a",
        help="Agent to use for sending.",
    ),
    mentions: str = typer.Option(
        "User",
        "--mentions",
        "-m",
        help="Comma-separated list of participants to mention.",
    ),
    msg_type: str = typer.Option(
        "message",
        "--type",
        "-t",
        help="Message type: message, thought, error, or task.",
    ),
) -> None:
    """Send a message to a room.

    Example:
        thenvoi-cli rooms send room-123 "Hello!" --agent my-agent
        thenvoi-cli rooms send room-123 "Analysis done" --agent my-agent --mentions User,Admin
        echo "Long message" | thenvoi-cli rooms send room-123 - --agent my-agent
    """
    # Handle stdin input
    if message == "-":
        message = sys.stdin.read().strip()
        if not message:
            console.print("[red]Error:[/red] No message provided via stdin")
            raise typer.Exit(1)

    # Parse mentions
    mention_names = [m.strip() for m in mentions.split(",") if m.strip()]

    async def _send() -> dict:
        config = ConfigManager()
        agent_id, api_key = config.load_agent(agent_name)
        client = SDKClient(agent_id=agent_id, api_key=api_key)

        await client.connect()
        try:
            tools = client.get_tools(room_id)
            if msg_type == "message":
                # Resolve mention names to IDs (workaround for SDK cache bug)
                participants = await tools.get_participants()
                name_to_id = {p["name"]: p["id"] for p in participants}
                resolved_mentions = []
                for name in mention_names:
                    pid = name_to_id.get(name)
                    if not pid:
                        available = list(name_to_id.keys())
                        raise ValueError(f"Unknown participant '{name}'. Available: {available}")
                    resolved_mentions.append({"id": pid, "name": name})
                return await tools.send_message(message, mentions=resolved_mentions)
            else:
                return await tools.send_event(message, message_type=msg_type)
        finally:
            await client.disconnect()

    try:
        result = run_async(_send())
        msg_id = result.get("id", "success")
        console.print(f"[green]Sent[/green] message (ID: {msg_id})")
    except ConfigurationError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to send message: {e}")
        raise typer.Exit(1)


@app.command("create")
def create_room(
    agent_name: str = typer.Option(
        ...,
        "--agent",
        "-a",
        help="Agent to use for creation.",
    ),
    task_id: Optional[str] = typer.Option(
        None,
        "--task-id",
        help="Task ID to associate with the room.",
    ),
    ctx: typer.Context = typer.Option(None),
) -> None:
    """Create a new chat room.

    Example:
        thenvoi-cli rooms create --agent my-agent
        thenvoi-cli rooms create --agent my-agent --task-id task-456
    """
    fmt = ctx.obj.get("format", OutputFormat.TABLE) if ctx.obj else OutputFormat.TABLE

    async def _create() -> str:
        config = ConfigManager()
        agent_id, api_key = config.load_agent(agent_name)
        client = SDKClient(agent_id=agent_id, api_key=api_key)

        await client.connect()
        try:
            tools = client.get_tools()
            return await tools.create_chatroom(task_id=task_id)
        finally:
            await client.disconnect()

    try:
        room_id = run_async(_create())

        if fmt == OutputFormat.JSON:
            import json

            console.print(json.dumps({"room_id": room_id}))
        else:
            console.print(f"[green]Created[/green] room: {room_id}")
    except ConfigurationError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to create room: {e}")
        raise typer.Exit(1)


@app.command("info")
def room_info(
    room_id: str = typer.Argument(..., help="Room ID to get info for."),
    agent_name: str = typer.Option(
        ...,
        "--agent",
        "-a",
        help="Agent to use for the request.",
    ),
    ctx: typer.Context = typer.Option(None),
) -> None:
    """Get detailed information about a room.

    Example:
        thenvoi-cli rooms info room-123 --agent my-agent
    """
    fmt = ctx.obj.get("format", OutputFormat.TABLE) if ctx.obj else OutputFormat.TABLE

    async def _info() -> dict:
        config = ConfigManager()
        agent_id, api_key = config.load_agent(agent_name)
        client = SDKClient(agent_id=agent_id, api_key=api_key)

        await client.connect()
        try:
            tools = client.get_tools(room_id)
            participants = await tools.get_participants()
            return {
                "room_id": room_id,
                "participants": participants,
            }
        finally:
            await client.disconnect()

    try:
        info = run_async(_info())

        if fmt == OutputFormat.JSON:
            import json

            console.print(json.dumps(info, indent=2, default=str))
        else:
            console.print(f"[bold]Room ID:[/bold] {info['room_id']}")
            console.print(f"[bold]Participants:[/bold]")
            for p in info.get("participants", []):
                name = p.get("name", "Unknown")
                role = p.get("role", "member")
                console.print(f"  - {name} ({role})")
    except ConfigurationError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
