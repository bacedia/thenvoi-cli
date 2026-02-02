"""Test command for connection testing."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import typer
from rich.console import Console

from thenvoi_cli.config_manager import ConfigManager
from thenvoi_cli.exceptions import AgentNotFoundError, InvalidConfigError

console = Console()


@dataclass
class CheckResult:
    """Result of a configuration check."""

    name: str
    passed: bool
    message: str
    details: str | None = None


def test(
    agent_name: str = typer.Argument(..., help="Agent to test."),
    config_only: bool = typer.Option(
        False,
        "--config-only",
        "-c",
        help="Only validate configuration (skip network tests).",
    ),
    ctx: typer.Context = typer.Option(None),
) -> None:
    """Test agent configuration and connectivity.

    Validates configuration and optionally tests connection to the
    Thenvoi platform.

    Example:
        thenvoi-cli test my-agent
        thenvoi-cli test my-agent --config-only
    """
    verbose = ctx.obj.get("verbosity", 0) >= 1 if ctx.obj else False

    console.print(f"Testing agent '[cyan]{agent_name}[/cyan]'...\n")

    checks: list[CheckResult] = []

    # Configuration checks
    console.print("[bold]Configuration:[/bold]")
    checks.append(_check_config_exists(agent_name))
    checks.append(_check_agent_exists(agent_name))
    checks.append(_check_uuid_format(agent_name))
    checks.append(_check_env_vars())

    for check in checks:
        _display_check(check, verbose)

    if not config_only:
        # Network checks
        console.print("\n[bold]Connectivity:[/bold]")
        net_checks: list[CheckResult] = []

        # Only run network tests if config passed
        config_passed = all(c.passed for c in checks if "Config" in c.name or "Agent" in c.name)
        if config_passed:
            import asyncio

            net_checks.append(asyncio.run(_check_rest_connectivity(agent_name)))
            net_checks.append(asyncio.run(_check_auth(agent_name)))

            for check in net_checks:
                _display_check(check, verbose)
            checks.extend(net_checks)
        else:
            console.print("  [yellow]Skipped[/yellow] (fix configuration errors first)")

    # Summary
    console.print()
    passed = sum(1 for c in checks if c.passed)
    total = len(checks)

    if all(c.passed for c in checks):
        console.print(f"[green]All {total} checks passed[/green]")
        raise typer.Exit(0)
    else:
        failed = total - passed
        console.print(f"[red]{failed} of {total} checks failed[/red]")
        raise typer.Exit(1)


def _display_check(check: CheckResult, verbose: bool) -> None:
    """Display a check result."""
    status = "[green]PASS[/green]" if check.passed else "[red]FAIL[/red]"
    console.print(f"  {status} {check.name}: {check.message}")
    if verbose and check.details:
        console.print(f"       [dim]{check.details}[/dim]")


def _check_config_exists(agent_name: str) -> CheckResult:
    """Check if configuration file exists."""
    manager = ConfigManager()
    if manager.config_exists():
        return CheckResult(
            name="Config file",
            passed=True,
            message="Found",
            details=str(manager.config_path.absolute()),
        )
    else:
        return CheckResult(
            name="Config file",
            passed=False,
            message="Not found",
            details=f"Expected at: {manager.config_path.absolute()}",
        )


def _check_agent_exists(agent_name: str) -> CheckResult:
    """Check if agent is configured."""
    manager = ConfigManager()
    try:
        manager.load_agent(agent_name)
        return CheckResult(
            name="Agent config",
            passed=True,
            message="Found",
        )
    except AgentNotFoundError:
        return CheckResult(
            name="Agent config",
            passed=False,
            message=f"Agent '{agent_name}' not found",
            details="Run 'thenvoi-cli config set' to add it",
        )
    except InvalidConfigError as e:
        return CheckResult(
            name="Agent config",
            passed=False,
            message=e.message,
        )


def _check_uuid_format(agent_name: str) -> CheckResult:
    """Check if agent ID is a valid UUID."""
    manager = ConfigManager()
    try:
        details = manager.get_agent_details(agent_name)
        agent_id = details.get("agent_id", "")

        if manager._validate_uuid(agent_id):
            return CheckResult(
                name="Agent ID format",
                passed=True,
                message="Valid UUID",
            )
        else:
            return CheckResult(
                name="Agent ID format",
                passed=False,
                message="Invalid UUID format",
                details=f"Got: {agent_id[:20]}..." if len(agent_id) > 20 else f"Got: {agent_id}",
            )
    except AgentNotFoundError:
        return CheckResult(
            name="Agent ID format",
            passed=False,
            message="Cannot validate (agent not found)",
        )


def _check_env_vars() -> CheckResult:
    """Check required environment variables."""
    required = ["THENVOI_REST_URL", "THENVOI_WS_URL"]
    missing = [var for var in required if not os.getenv(var)]

    if not missing:
        return CheckResult(
            name="Environment vars",
            passed=True,
            message="All required variables set",
            details=", ".join(required),
        )
    else:
        return CheckResult(
            name="Environment vars",
            passed=False,
            message=f"Missing: {', '.join(missing)}",
            details="Export these variables before running",
        )


async def _check_rest_connectivity(agent_name: str) -> CheckResult:
    """Check REST API connectivity."""
    rest_url = os.getenv("THENVOI_REST_URL")
    if not rest_url:
        return CheckResult(
            name="REST API",
            passed=False,
            message="THENVOI_REST_URL not set",
        )

    try:
        import httpx
        import time

        start = time.time()
        async with httpx.AsyncClient() as client:
            # Try health endpoint or just the base URL
            response = await client.get(
                f"{rest_url.rstrip('/')}/",
                timeout=10.0,
                follow_redirects=True,
            )
            elapsed = int((time.time() - start) * 1000)

            if response.status_code < 500:
                return CheckResult(
                    name="REST API",
                    passed=True,
                    message=f"Reachable ({elapsed}ms)",
                    details=rest_url,
                )
            else:
                return CheckResult(
                    name="REST API",
                    passed=False,
                    message=f"Server error (status {response.status_code})",
                    details=rest_url,
                )
    except httpx.ConnectError as e:
        return CheckResult(
            name="REST API",
            passed=False,
            message="Connection failed",
            details=str(e),
        )
    except Exception as e:
        return CheckResult(
            name="REST API",
            passed=False,
            message=f"Error: {type(e).__name__}",
            details=str(e),
        )


async def _check_auth(agent_name: str) -> CheckResult:
    """Check authentication with the platform."""
    try:
        from thenvoi_cli.config_manager import ConfigManager
        from thenvoi_cli.sdk_client import SDKClient

        config = ConfigManager()
        agent_id, api_key = config.load_agent(agent_name)

        client = SDKClient(agent_id=agent_id, api_key=api_key)

        # Try to connect - this will validate credentials
        await client.connect()
        await client.disconnect()

        return CheckResult(
            name="Authentication",
            passed=True,
            message="Credentials accepted",
        )
    except Exception as e:
        error_str = str(e).lower()
        if "auth" in error_str or "401" in error_str or "403" in error_str:
            return CheckResult(
                name="Authentication",
                passed=False,
                message="Invalid credentials",
                details="Check your API key",
            )
        else:
            return CheckResult(
                name="Authentication",
                passed=False,
                message=f"Connection error",
                details=str(e),
            )
