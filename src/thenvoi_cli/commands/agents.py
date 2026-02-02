"""Agent management commands (requires User API key)."""

from __future__ import annotations

import os
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from thenvoi_cli.exceptions import ConfigurationError, MissingEnvironmentError
from thenvoi_cli.output import OutputFormat, mask_api_key

app = typer.Typer(help="Manage agents on the platform (requires User API key).")
console = Console()


def _get_user_api_key() -> str:
    """Get the user API key from environment."""
    key = os.getenv("THENVOI_API_KEY_USER")
    if not key:
        raise MissingEnvironmentError("THENVOI_API_KEY_USER")
    return key


def _get_rest_url() -> str:
    """Get the REST URL from environment."""
    url = os.getenv("THENVOI_REST_URL")
    if not url:
        raise MissingEnvironmentError("THENVOI_REST_URL")
    return url


async def _get_user_client():
    """Get an async REST client with user API key."""
    from thenvoi_rest import AsyncRestClient

    return AsyncRestClient(
        api_key=_get_user_api_key(),
        base_url=_get_rest_url(),
    )


@app.command("list")
def list_agents(
    ctx: typer.Context = typer.Option(None),
) -> None:
    """List all agents you own.

    Requires THENVOI_API_KEY_USER environment variable.

    Example:
        thenvoi-cli agents list
        thenvoi-cli agents list --format json
    """
    import asyncio

    fmt = ctx.obj.get("format", OutputFormat.TABLE) if ctx.obj else OutputFormat.TABLE

    async def _list():
        client = await _get_user_client()
        response = await client.human_api.list_my_agents()
        return response.data or []

    try:
        agents = asyncio.run(_list())
    except MissingEnvironmentError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        console.print(f"[yellow]Hint:[/yellow] {e.hint}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    if not agents:
        if fmt == OutputFormat.JSON:
            console.print("[]")
        else:
            console.print("No agents found")
            console.print("[dim]Create one with: thenvoi-cli agents register[/dim]")
        return

    if fmt == OutputFormat.JSON:
        import json

        data = [
            {
                "id": str(agent.id),
                "name": agent.name,
                "description": getattr(agent, "description", ""),
                "api_key_masked": mask_api_key(getattr(agent, "api_key", "") or ""),
            }
            for agent in agents
        ]
        console.print(json.dumps(data, indent=2))
    elif fmt == OutputFormat.TABLE:
        table = Table(title="Your Agents")
        table.add_column("ID", style="cyan")
        table.add_column("Name")
        table.add_column("Description")

        for agent in agents:
            table.add_row(
                str(agent.id),
                agent.name,
                getattr(agent, "description", "")[:40],
            )
        console.print(table)
    else:  # PLAIN
        for agent in agents:
            console.print(f"{agent.id}: {agent.name}")


@app.command("register")
def register_agent(
    name: str = typer.Option(..., "--name", "-n", help="Agent name"),
    description: str = typer.Option("", "--description", "-d", help="Agent description"),
    save_config: bool = typer.Option(
        True,
        "--save/--no-save",
        help="Save credentials to agent_config.yaml",
    ),
    ctx: typer.Context = typer.Option(None),
) -> None:
    """Register a new agent on the platform.

    Requires THENVOI_API_KEY_USER environment variable.

    Example:
        thenvoi-cli agents register --name "My Bot" --description "A helpful assistant"
    """
    import asyncio

    fmt = ctx.obj.get("format", OutputFormat.TABLE) if ctx.obj else OutputFormat.TABLE

    async def _register():
        client = await _get_user_client()
        from thenvoi_rest import AgentRequest

        response = await client.human_api.register_my_agent(
            agent=AgentRequest(name=name, description=description)
        )
        return response.data

    try:
        agent = asyncio.run(_register())
    except MissingEnvironmentError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        console.print(f"[yellow]Hint:[/yellow] {e.hint}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    agent_id = str(agent.id)
    api_key = getattr(agent, "api_key", None)

    if fmt == OutputFormat.JSON:
        import json

        console.print(json.dumps({
            "id": agent_id,
            "name": agent.name,
            "api_key": api_key,  # Show full key in JSON for scripting
        }, indent=2))
    else:
        console.print(f"[green]Registered[/green] agent '{agent.name}'")
        console.print(f"[bold]Agent ID:[/bold] {agent_id}")
        if api_key:
            console.print(f"[bold]API Key:[/bold] {api_key}")
            console.print("[yellow]Save this API key now - it won't be shown again![/yellow]")

    # Save to config
    if save_config and api_key:
        from thenvoi_cli.config_manager import ConfigManager

        config_name = name.lower().replace(" ", "-")
        manager = ConfigManager()

        try:
            manager.save_agent(config_name, agent_id, api_key)
            console.print(f"\n[green]Saved[/green] to config as '{config_name}'")
            console.print(f"Run with: thenvoi-cli run {config_name}")
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Could not save to config: {e}")
            console.print("Save manually with:")
            console.print(f"  thenvoi-cli config set {config_name} --agent-id {agent_id} --api-key {api_key}")


@app.command("delete")
def delete_agent(
    agent_id: str = typer.Argument(..., help="Agent ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete an agent from the platform.

    Requires THENVOI_API_KEY_USER environment variable.

    Example:
        thenvoi-cli agents delete 12345678-1234-1234-1234-123456789012
    """
    import asyncio

    if not force:
        confirm = typer.confirm(f"Delete agent {agent_id}? This cannot be undone.")
        if not confirm:
            raise typer.Abort()

    async def _delete():
        client = await _get_user_client()
        await client.human_api.delete_my_agent(id=agent_id, force=True)

    try:
        asyncio.run(_delete())
        console.print(f"[green]Deleted[/green] agent {agent_id}")
    except MissingEnvironmentError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        console.print(f"[yellow]Hint:[/yellow] {e.hint}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("info")
def agent_info(
    agent_id: Optional[str] = typer.Argument(None, help="Agent ID (or uses configured agent)"),
    agent_name: Optional[str] = typer.Option(None, "--agent", "-a", help="Agent name from config"),
    ctx: typer.Context = typer.Option(None),
) -> None:
    """Get information about an agent.

    Can use either agent_id directly or --agent to look up from config.

    Example:
        thenvoi-cli agents info 12345678-1234-1234-1234-123456789012
        thenvoi-cli agents info --agent my-agent
    """
    import asyncio

    fmt = ctx.obj.get("format", OutputFormat.TABLE) if ctx.obj else OutputFormat.TABLE

    # Resolve agent_id from config if needed
    if not agent_id and agent_name:
        from thenvoi_cli.config_manager import ConfigManager

        manager = ConfigManager()
        agent_id, _ = manager.load_agent(agent_name)
    elif not agent_id:
        console.print("[red]Error:[/red] Provide agent_id or --agent name")
        raise typer.Exit(1)

    async def _info():
        # Use agent API to get agent's own info
        from thenvoi_rest import AsyncRestClient

        # We need the agent's API key for this
        if agent_name:
            from thenvoi_cli.config_manager import ConfigManager

            manager = ConfigManager()
            _, api_key = manager.load_agent(agent_name)
        else:
            console.print("[yellow]Note:[/yellow] Using user API - limited info available")
            # Can't get detailed info without agent's own API key
            return None

        client = AsyncRestClient(
            api_key=api_key,
            base_url=_get_rest_url(),
        )
        response = await client.agent_api.get_agent_me()
        return response.data

    try:
        agent = asyncio.run(_info())
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    if not agent:
        console.print(f"Agent ID: {agent_id}")
        console.print("[dim]Use --agent <name> to get full details[/dim]")
        return

    if fmt == OutputFormat.JSON:
        import json

        data = {
            "id": str(agent.id),
            "name": agent.name,
            "description": getattr(agent, "description", ""),
        }
        console.print(json.dumps(data, indent=2))
    else:
        console.print(f"[bold]Agent ID:[/bold] {agent.id}")
        console.print(f"[bold]Name:[/bold] {agent.name}")
        if hasattr(agent, "description") and agent.description:
            console.print(f"[bold]Description:[/bold] {agent.description}")
