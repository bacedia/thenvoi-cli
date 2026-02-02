"""Peer discovery command."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from thenvoi_cli.config_manager import ConfigManager
from thenvoi_cli.exceptions import ConfigurationError
from thenvoi_cli.output import OutputFormat
from thenvoi_cli.sdk_client import SDKClient, run_async

console = Console()


def peers(
    agent_name: str = typer.Option(
        ...,
        "--agent",
        "-a",
        help="Agent to use for peer discovery.",
    ),
    page: int = typer.Option(
        1,
        "--page",
        "-p",
        help="Page number for pagination.",
    ),
    page_size: int = typer.Option(
        50,
        "--page-size",
        help="Number of results per page.",
    ),
    ctx: typer.Context = typer.Option(None),
) -> None:
    """List available peers for multi-agent collaboration.

    Peers are other agents that can be added as participants to rooms.

    Example:
        thenvoi-cli peers --agent my-agent
        thenvoi-cli peers --agent my-agent --page 2 --page-size 20
        thenvoi-cli peers --agent my-agent --format json
    """
    fmt = ctx.obj.get("format", OutputFormat.TABLE) if ctx.obj else OutputFormat.TABLE

    async def _peers() -> dict:
        config = ConfigManager()
        agent_id, api_key = config.load_agent(agent_name)
        client = SDKClient(agent_id=agent_id, api_key=api_key)

        await client.connect()
        try:
            tools = client.get_tools()
            return await tools.lookup_peers(page=page, page_size=page_size)
        finally:
            await client.disconnect()

    try:
        result = run_async(_peers())
    except ConfigurationError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    peers_list = result.get("peers", result.get("data", []))
    total = result.get("total", len(peers_list))

    if not peers_list:
        if fmt == OutputFormat.JSON:
            console.print('{"peers": [], "total": 0}')
        else:
            console.print("No peers found")
        return

    if fmt == OutputFormat.JSON:
        import json

        console.print(json.dumps(result, indent=2, default=str))
    elif fmt == OutputFormat.TABLE:
        table = Table(title=f"Available Peers (Page {page}, Total: {total})")
        table.add_column("Name", style="cyan")
        table.add_column("Description")
        table.add_column("Status")

        for peer in peers_list:
            table.add_row(
                peer.get("name", "Unknown"),
                peer.get("description", "")[:50],
                peer.get("status", ""),
            )
        console.print(table)

        # Show pagination info
        if len(peers_list) == page_size:
            console.print(f"\n[dim]Use --page {page + 1} to see more[/dim]")
    else:  # PLAIN
        for peer in peers_list:
            console.print(f"{peer.get('name', 'Unknown')}: {peer.get('description', '')}")
