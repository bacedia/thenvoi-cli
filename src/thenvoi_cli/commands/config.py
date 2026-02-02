"""Configuration management commands."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from thenvoi_cli.config_manager import ConfigManager
from thenvoi_cli.exceptions import AgentNotFoundError, InvalidConfigError
from thenvoi_cli.output import OutputFormat, mask_api_key, mask_uuid

app = typer.Typer(help="Manage agent configurations.")
console = Console()


@app.command("set")
def set_config(
    name: str = typer.Argument(..., help="Agent name for configuration."),
    agent_id: str = typer.Option(
        ...,
        "--agent-id",
        "-i",
        help="Agent UUID from the Thenvoi platform.",
    ),
    api_key: str = typer.Option(
        ...,
        "--api-key",
        "-k",
        help="Agent API key.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing agent without warning.",
    ),
) -> None:
    """Save agent configuration.

    Example:
        thenvoi-cli config set my-agent --agent-id abc-123 --api-key sk-...
    """
    manager = ConfigManager()

    # Check for existing
    existing_agents = manager.list_agents()
    if name in existing_agents and not force:
        overwrite = typer.confirm(
            f"Agent '{name}' already exists. Overwrite?",
            default=False,
        )
        if not overwrite:
            raise typer.Abort()

    try:
        is_new = manager.save_agent(name, agent_id, api_key, force=force)
        action = "Created" if is_new else "Updated"
        console.print(f"[green]{action}[/green] configuration for '{name}'")

        # Check file permissions
        if not manager.check_permissions():
            console.print(
                "[yellow]Warning:[/yellow] Config file has insecure permissions. "
                "Consider running: chmod 600 agent_config.yaml"
            )
    except InvalidConfigError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)


@app.command("list")
def list_configs(
    ctx: typer.Context,
    format: Optional[OutputFormat] = typer.Option(
        None,
        "--format",
        "-f",
        help="Output format (overrides global).",
    ),
) -> None:
    """List all configured agents.

    Example:
        thenvoi-cli config list
        thenvoi-cli config list --format json
    """
    fmt = format or ctx.obj.get("format", OutputFormat.TABLE)
    manager = ConfigManager()
    agents = manager.list_agents()

    if not agents:
        if fmt == OutputFormat.JSON:
            console.print("[]")
        else:
            console.print("No agents configured.")
            console.print("Add one with: thenvoi-cli config set <name> --agent-id <id> --api-key <key>")
        return

    if fmt == OutputFormat.JSON:
        import json

        data = []
        for name in agents:
            details = manager.get_agent_details(name)
            data.append({
                "name": name,
                "agent_id": details.get("agent_id"),
                "api_key_masked": mask_api_key(details.get("api_key", "")),
            })
        console.print(json.dumps(data, indent=2))
    elif fmt == OutputFormat.TABLE:
        table = Table(title="Configured Agents")
        table.add_column("Name", style="cyan")
        table.add_column("Agent ID")
        table.add_column("API Key")

        for name in agents:
            details = manager.get_agent_details(name)
            table.add_row(
                name,
                mask_uuid(details.get("agent_id", "")),
                mask_api_key(details.get("api_key", "")),
            )
        console.print(table)
    else:  # PLAIN
        for name in agents:
            details = manager.get_agent_details(name)
            console.print(
                f"{name}: {mask_uuid(details.get('agent_id', ''))} | {mask_api_key(details.get('api_key', ''))}"
            )


@app.command("show")
def show_config(
    name: str = typer.Argument(..., help="Agent name to show."),
    reveal: bool = typer.Option(
        False,
        "--reveal",
        "-r",
        help="Show full API key (use with caution).",
    ),
    ctx: typer.Context = typer.Option(None),
) -> None:
    """Show configuration for a specific agent.

    Example:
        thenvoi-cli config show my-agent
        thenvoi-cli config show my-agent --reveal
    """
    manager = ConfigManager()

    try:
        details = manager.get_agent_details(name)
    except AgentNotFoundError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        if e.hint:
            console.print(f"[yellow]Hint:[/yellow] {e.hint}")
        raise typer.Exit(1)

    api_key = details.get("api_key", "")
    displayed_key = api_key if reveal else mask_api_key(api_key)

    console.print(f"[bold]Agent:[/bold] {name}")
    console.print(f"[bold]Agent ID:[/bold] {details.get('agent_id', '')}")
    console.print(f"[bold]API Key:[/bold] {displayed_key}")

    if not reveal:
        console.print("\n[dim]Use --reveal to show full API key[/dim]")


@app.command("delete")
def delete_config(
    name: str = typer.Argument(..., help="Agent name to delete."),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Delete without confirmation.",
    ),
) -> None:
    """Delete an agent configuration.

    Example:
        thenvoi-cli config delete my-agent
        thenvoi-cli config delete my-agent --force
    """
    manager = ConfigManager()

    # Check if agent exists
    if name not in manager.list_agents():
        console.print(f"[red]Error:[/red] Agent '{name}' not found")
        raise typer.Exit(1)

    if not force:
        confirm = typer.confirm(f"Delete configuration for '{name}'?", default=False)
        if not confirm:
            raise typer.Abort()

    if manager.delete_agent(name):
        console.print(f"[green]Deleted[/green] configuration for '{name}'")
    else:
        console.print(f"[red]Error:[/red] Failed to delete '{name}'")
        raise typer.Exit(1)


@app.command("validate")
def validate_config(
    name: Optional[str] = typer.Argument(
        None,
        help="Specific agent to validate, or all if not specified.",
    ),
) -> None:
    """Validate agent configuration.

    Example:
        thenvoi-cli config validate
        thenvoi-cli config validate my-agent
    """
    manager = ConfigManager()
    errors = manager.validate_config(name)

    if errors:
        console.print("[red]Validation errors:[/red]")
        for error in errors:
            console.print(f"  - {error}")
        raise typer.Exit(1)
    else:
        scope = f"agent '{name}'" if name else "all agents"
        console.print(f"[green]Configuration valid[/green] for {scope}")

        # Also check permissions
        if not manager.check_permissions():
            console.print(
                "[yellow]Warning:[/yellow] Config file has insecure permissions"
            )


@app.command("path")
def show_path() -> None:
    """Show the configuration file path.

    Example:
        thenvoi-cli config path
    """
    manager = ConfigManager()
    console.print(str(manager.config_path.absolute()))

    if manager.config_exists():
        console.print(f"[dim]File exists: Yes[/dim]")
        if manager.check_permissions():
            console.print(f"[dim]Permissions: Secure[/dim]")
        else:
            console.print(f"[yellow]Permissions: Insecure (recommend chmod 600)[/yellow]")
    else:
        console.print(f"[dim]File exists: No[/dim]")
