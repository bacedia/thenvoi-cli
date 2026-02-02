"""Output formatting utilities for thenvoi-cli."""

from __future__ import annotations

import json
import os
from enum import Enum
from typing import Any

from rich.console import Console
from rich.table import Table


class OutputFormat(str, Enum):
    """Output format options."""

    JSON = "json"
    TABLE = "table"
    PLAIN = "plain"


class OutputFormatter:
    """Handles formatting and displaying output in various formats."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()
        self._no_color = os.getenv("NO_COLOR") is not None

    def format_dict(self, data: dict[str, Any], fmt: OutputFormat) -> str:
        """Format a dictionary for output."""
        if fmt == OutputFormat.JSON:
            return json.dumps(data, indent=2, default=str)
        elif fmt == OutputFormat.TABLE:
            table = Table(show_header=True)
            table.add_column("Key", style="cyan")
            table.add_column("Value")
            for key, value in data.items():
                table.add_row(str(key), str(value))
            # Capture table as string
            with self.console.capture() as capture:
                self.console.print(table)
            return capture.get()
        else:  # PLAIN
            lines = [f"{key}: {value}" for key, value in data.items()]
            return "\n".join(lines)

    def format_list(
        self,
        data: list[dict[str, Any]],
        fmt: OutputFormat,
        headers: list[str] | None = None,
    ) -> str:
        """Format a list of dictionaries for output."""
        if not data:
            if fmt == OutputFormat.JSON:
                return "[]"
            return "No results"

        if fmt == OutputFormat.JSON:
            return json.dumps(data, indent=2, default=str)

        # Infer headers from first item if not provided
        if headers is None:
            headers = list(data[0].keys())

        if fmt == OutputFormat.TABLE:
            table = Table(show_header=True)
            for header in headers:
                table.add_column(header.replace("_", " ").title(), style="cyan")
            for row in data:
                table.add_row(*[str(row.get(h, "")) for h in headers])
            with self.console.capture() as capture:
                self.console.print(table)
            return capture.get()
        else:  # PLAIN
            lines = []
            for row in data:
                parts = [f"{h}: {row.get(h, '')}" for h in headers]
                lines.append(" | ".join(parts))
            return "\n".join(lines)

    def print_dict(self, data: dict[str, Any], fmt: OutputFormat) -> None:
        """Print a formatted dictionary."""
        output = self.format_dict(data, fmt)
        if fmt == OutputFormat.TABLE:
            # Already printed by capture
            self.console.print(output, highlight=False)
        else:
            self.console.print(output, highlight=False)

    def print_list(
        self,
        data: list[dict[str, Any]],
        fmt: OutputFormat,
        headers: list[str] | None = None,
    ) -> None:
        """Print a formatted list."""
        output = self.format_list(data, fmt, headers)
        self.console.print(output, highlight=False)

    def success(self, message: str) -> None:
        """Print a success message."""
        if self._no_color:
            self.console.print(f"OK: {message}")
        else:
            self.console.print(f"[green]OK:[/green] {message}")

    def error(self, message: str) -> None:
        """Print an error message."""
        if self._no_color:
            self.console.print(f"Error: {message}", style="")
        else:
            self.console.print(f"[red]Error:[/red] {message}")

    def warning(self, message: str) -> None:
        """Print a warning message."""
        if self._no_color:
            self.console.print(f"Warning: {message}")
        else:
            self.console.print(f"[yellow]Warning:[/yellow] {message}")

    def info(self, message: str) -> None:
        """Print an info message."""
        if self._no_color:
            self.console.print(message)
        else:
            self.console.print(f"[dim]{message}[/dim]")


# Global formatter instance
formatter = OutputFormatter()


def mask_api_key(key: str) -> str:
    """Mask an API key, showing only the last 4 characters."""
    if len(key) <= 8:
        return "****"
    return f"{'*' * (len(key) - 4)}{key[-4:]}"


def mask_uuid(uuid: str) -> str:
    """Mask a UUID, showing only first and last segments."""
    parts = uuid.split("-")
    if len(parts) != 5:
        return uuid
    return f"{parts[0]}-****-****-****-{parts[4]}"
