"""Custom exceptions for thenvoi-cli."""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Callable, ParamSpec, TypeVar

import typer

if TYPE_CHECKING:
    pass

P = ParamSpec("P")
R = TypeVar("R")


class ThenvoiCLIError(Exception):
    """Base exception for thenvoi-cli errors."""

    exit_code: int = 1
    hint: str | None = None

    def __init__(self, message: str, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if hint:
            self.hint = hint


class ConfigurationError(ThenvoiCLIError):
    """Error related to configuration."""

    pass


class AgentNotFoundError(ConfigurationError):
    """Agent not found in configuration."""

    def __init__(self, agent_name: str) -> None:
        self.agent_name = agent_name
        super().__init__(
            f"Agent '{agent_name}' not found in configuration",
            hint="Run 'thenvoi-cli config list' to see available agents, "
            "or 'thenvoi-cli config set' to add a new agent.",
        )


class InvalidConfigError(ConfigurationError):
    """Invalid configuration value."""

    pass


class MissingEnvironmentError(ConfigurationError):
    """Required environment variable is missing."""

    def __init__(self, var_name: str) -> None:
        self.var_name = var_name
        super().__init__(
            f"Required environment variable '{var_name}' is not set",
            hint=f"Set the variable: export {var_name}=<value>",
        )


class ConnectionError(ThenvoiCLIError):
    """Error connecting to the Thenvoi platform."""

    exit_code = 2


class AuthenticationError(ThenvoiCLIError):
    """Authentication failed."""

    exit_code = 3

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(
            message,
            hint="Check your API key with 'thenvoi-cli config show <agent>' "
            "or regenerate it on the Thenvoi platform.",
        )


class AdapterError(ThenvoiCLIError):
    """Error related to adapters."""

    pass


class MissingDependencyError(AdapterError):
    """Required adapter dependencies are not installed."""

    def __init__(self, adapter_name: str, dependencies: list[str]) -> None:
        self.adapter_name = adapter_name
        self.dependencies = dependencies
        deps_str = ", ".join(dependencies)
        super().__init__(
            f"Adapter '{adapter_name}' requires missing dependencies: {deps_str}",
            hint=f"Install with: pip install thenvoi-cli[{adapter_name}]",
        )


class RoomNotFoundError(ThenvoiCLIError):
    """Room not found."""

    def __init__(self, room_id: str) -> None:
        self.room_id = room_id
        super().__init__(f"Room '{room_id}' not found")


class AgentNotRunningError(ThenvoiCLIError):
    """Agent is not currently running."""

    def __init__(self, agent_name: str) -> None:
        self.agent_name = agent_name
        super().__init__(
            f"Agent '{agent_name}' is not running",
            hint=f"Start the agent with: thenvoi-cli run {agent_name}",
        )


def handle_errors(debug: bool = False) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to handle exceptions and display user-friendly errors."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return func(*args, **kwargs)
            except ThenvoiCLIError as e:
                typer.secho(f"Error: {e.message}", fg=typer.colors.RED, err=True)
                if e.hint:
                    typer.secho(f"Hint: {e.hint}", fg=typer.colors.YELLOW, err=True)
                if debug:
                    raise
                raise typer.Exit(e.exit_code) from None
            except KeyboardInterrupt:
                typer.echo("\nInterrupted", err=True)
                raise typer.Exit(130) from None
            except Exception as e:
                typer.secho(f"Unexpected error: {e}", fg=typer.colors.RED, err=True)
                if debug:
                    raise
                typer.secho(
                    "Run with --debug for full traceback",
                    fg=typer.colors.YELLOW,
                    err=True,
                )
                raise typer.Exit(1) from None

        return wrapper

    return decorator
