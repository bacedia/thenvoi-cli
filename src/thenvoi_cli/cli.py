"""Main CLI entry point for thenvoi-cli."""

from __future__ import annotations

import os
from typing import Optional

import typer
from rich.console import Console

from thenvoi_cli import __version__
from thenvoi_cli.logging_config import setup_logging
from thenvoi_cli.output import OutputFormat

# Create the main app
app = typer.Typer(
    name="thenvoi-cli",
    help="CLI for the Thenvoi AI agent platform.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Console for output
console = Console()

# Global state
state: dict[str, object] = {}


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"thenvoi-cli {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
    verbose: int = typer.Option(
        0,
        "--verbose",
        "-v",
        count=True,
        help="Increase verbosity. Use -v for info, -vv for debug.",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Only show errors.",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug mode with full tracebacks.",
    ),
    log_file: Optional[str] = typer.Option(
        None,
        "--log-file",
        help="Write logs to file.",
    ),
    format: OutputFormat = typer.Option(
        OutputFormat.TABLE,
        "--format",
        "-f",
        help="Output format.",
    ),
) -> None:
    """Thenvoi CLI - AI agent platform interface.

    Manage and run AI agents on the Thenvoi collaborative platform.
    """
    # Determine verbosity level
    if quiet:
        verbosity = -1
    elif debug:
        verbosity = 2
    else:
        verbosity = verbose

    # Set up logging
    logger = setup_logging(
        verbosity=verbosity,
        log_file=log_file,
        no_color=os.getenv("NO_COLOR") is not None,
    )

    # Store state for subcommands
    ctx.ensure_object(dict)
    ctx.obj["logger"] = logger
    ctx.obj["debug"] = debug
    ctx.obj["format"] = format
    ctx.obj["verbosity"] = verbosity


# Import and register command groups
from thenvoi_cli.commands import adapters as adapters_cmd
from thenvoi_cli.commands import config as config_cmd
from thenvoi_cli.commands import participants as participants_cmd
from thenvoi_cli.commands import peers as peers_cmd
from thenvoi_cli.commands import rooms as rooms_cmd
from thenvoi_cli.commands import run as run_cmd
from thenvoi_cli.commands import status as status_cmd
from thenvoi_cli.commands import test as test_cmd

app.add_typer(config_cmd.app, name="config")
app.add_typer(rooms_cmd.app, name="rooms")
app.add_typer(participants_cmd.app, name="participants")
app.add_typer(adapters_cmd.app, name="adapters")

# Add standalone commands
app.command(name="run")(run_cmd.run)
app.command(name="status")(status_cmd.status)
app.command(name="stop")(status_cmd.stop)
app.command(name="test")(test_cmd.test)
app.command(name="peers")(peers_cmd.peers)


# Completion command
@app.command()
def completion(
    shell: str = typer.Argument(
        ...,
        help="Shell type: bash, zsh, or fish.",
    ),
) -> None:
    """Generate shell completion script.

    Example:
        thenvoi-cli completion bash >> ~/.bashrc
        thenvoi-cli completion zsh >> ~/.zshrc
        thenvoi-cli completion fish > ~/.config/fish/completions/thenvoi-cli.fish
    """
    import subprocess
    import sys

    # Use typer's built-in completion generation
    script_name = "thenvoi-cli"

    if shell == "bash":
        result = subprocess.run(
            [sys.executable, "-m", "typer", "thenvoi_cli.cli", "utils", "completion", "--name", script_name, "--shell", "bash"],
            capture_output=True,
            text=True,
        )
    elif shell == "zsh":
        result = subprocess.run(
            [sys.executable, "-m", "typer", "thenvoi_cli.cli", "utils", "completion", "--name", script_name, "--shell", "zsh"],
            capture_output=True,
            text=True,
        )
    elif shell == "fish":
        result = subprocess.run(
            [sys.executable, "-m", "typer", "thenvoi_cli.cli", "utils", "completion", "--name", script_name, "--shell", "fish"],
            capture_output=True,
            text=True,
        )
    else:
        console.print(f"[red]Unknown shell: {shell}[/red]")
        console.print("Supported shells: bash, zsh, fish")
        raise typer.Exit(1)

    if result.returncode == 0:
        console.print(result.stdout)
    else:
        # Fallback: generate basic completion
        console.print(f"# Completion for {shell} not available via typer")
        console.print(f"# Install shell completions manually")


if __name__ == "__main__":
    app()
