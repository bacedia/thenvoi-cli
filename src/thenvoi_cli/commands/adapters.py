"""Adapter discovery commands."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from thenvoi_cli.adapter_registry import ADAPTERS, registry
from thenvoi_cli.output import OutputFormat

app = typer.Typer(help="Discover and learn about adapters.")
console = Console()


@app.command("list")
def list_adapters(
    ctx: typer.Context = typer.Option(None),
) -> None:
    """List all available adapters.

    Example:
        thenvoi-cli adapters list
        thenvoi-cli adapters list --format json
    """
    fmt = ctx.obj.get("format", OutputFormat.TABLE) if ctx.obj else OutputFormat.TABLE

    data = []
    for name in registry.list_adapters():
        info = registry.get_adapter_info(name)
        if info:
            available = registry.is_available(name)
            data.append({
                "name": name,
                "description": info.description,
                "available": available,
                "default_model": info.default_model or "-",
            })

    if fmt == OutputFormat.JSON:
        import json

        console.print(json.dumps(data, indent=2))
    elif fmt == OutputFormat.TABLE:
        table = Table(title="Available Adapters")
        table.add_column("Name", style="cyan")
        table.add_column("Description")
        table.add_column("Ready")
        table.add_column("Default Model")

        for item in data:
            ready = "[green]Yes[/green]" if item["available"] else "[red]No[/red]"
            table.add_row(
                item["name"],
                item["description"],
                ready,
                item["default_model"],
            )
        console.print(table)
    else:  # PLAIN
        for item in data:
            status = "ready" if item["available"] else "missing deps"
            console.print(f"{item['name']}: {item['description']} ({status})")


@app.command("info")
def adapter_info(
    name: str = typer.Argument(..., help="Adapter name to get info for."),
) -> None:
    """Show detailed information about an adapter.

    Example:
        thenvoi-cli adapters info langgraph
        thenvoi-cli adapters info anthropic
    """
    info = registry.get_adapter_info(name)
    if not info:
        available = ", ".join(registry.list_adapters())
        console.print(f"[red]Error:[/red] Unknown adapter '{name}'")
        console.print(f"Available adapters: {available}")
        raise typer.Exit(1)

    available = registry.is_available(name)
    missing = registry.get_missing_deps(name)

    console.print(f"\n[bold cyan]{info.name}[/bold cyan]")
    console.print(f"  {info.description}\n")

    console.print(f"[bold]Status:[/bold] ", end="")
    if available:
        console.print("[green]Ready[/green]")
    else:
        console.print("[red]Missing dependencies[/red]")

    if info.default_model:
        console.print(f"[bold]Default Model:[/bold] {info.default_model}")

    console.print(f"\n[bold]Required Dependencies:[/bold]")
    for dep in info.required_deps:
        from thenvoi_cli.adapter_registry import _is_package_installed

        installed = _is_package_installed(dep)
        status = "[green]Installed[/green]" if installed else "[red]Missing[/red]"
        console.print(f"  {dep}: {status}")

    if info.env_vars:
        console.print(f"\n[bold]Required Environment Variables:[/bold]")
        import os

        for var in info.env_vars:
            is_set = os.getenv(var) is not None
            status = "[green]Set[/green]" if is_set else "[yellow]Not set[/yellow]"
            console.print(f"  {var}: {status}")

    if not available:
        console.print(f"\n[bold]Install dependencies with:[/bold]")
        console.print(f"  pip install thenvoi-cli[{name}]")

    console.print(f"\n[bold]Example usage:[/bold]")
    console.print(f"  thenvoi-cli run my-agent --adapter {name}")
    if info.default_model:
        console.print(f"  thenvoi-cli run my-agent --adapter {name} --model {info.default_model}")
