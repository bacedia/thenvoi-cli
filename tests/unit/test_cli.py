"""Tests for CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from thenvoi_cli.cli import app


class TestCLIBasics:
    """Tests for basic CLI functionality."""

    def test_version(self, cli_runner: CliRunner) -> None:
        """Test --version flag."""
        result = cli_runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "thenvoi-cli" in result.stdout
        assert "0.1.0" in result.stdout

    def test_help(self, cli_runner: CliRunner) -> None:
        """Test --help flag."""
        result = cli_runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "thenvoi-cli" in result.stdout
        assert "config" in result.stdout
        assert "run" in result.stdout
        assert "rooms" in result.stdout

    def test_no_args_shows_help(self, cli_runner: CliRunner) -> None:
        """Test that no args shows help."""
        result = cli_runner.invoke(app, [])

        # Should exit with help (no_args_is_help=True)
        assert result.exit_code == 0
        assert "Usage" in result.stdout


class TestConfigCommands:
    """Tests for config subcommands."""

    def test_config_list_empty(
        self, cli_runner: CliRunner, temp_config: Path
    ) -> None:
        """Test config list with no agents."""
        with patch("thenvoi_cli.commands.config.ConfigManager") as MockManager:
            MockManager.return_value.list_agents.return_value = []

            result = cli_runner.invoke(app, ["config", "list"])

            assert result.exit_code == 0
            assert "No agents configured" in result.stdout

    def test_config_list_with_agents(
        self, cli_runner: CliRunner, sample_config: Path
    ) -> None:
        """Test config list with agents."""
        with patch("thenvoi_cli.commands.config.ConfigManager") as MockManager:
            MockManager.return_value.list_agents.return_value = ["test-agent", "other-agent"]
            MockManager.return_value.get_agent_details.side_effect = [
                {"agent_id": "12345678-1234-1234-1234-123456789012", "api_key": "sk-test"},
                {"agent_id": "87654321-4321-4321-4321-210987654321", "api_key": "sk-other"},
            ]

            result = cli_runner.invoke(app, ["config", "list"])

            assert result.exit_code == 0
            assert "test-agent" in result.stdout

    def test_config_set(self, cli_runner: CliRunner, temp_config: Path) -> None:
        """Test config set command."""
        with patch("thenvoi_cli.commands.config.ConfigManager") as MockManager:
            MockManager.return_value.list_agents.return_value = []
            MockManager.return_value.save_agent.return_value = True
            MockManager.return_value.check_permissions.return_value = True

            result = cli_runner.invoke(app, [
                "config", "set", "new-agent",
                "--agent-id", "12345678-1234-1234-1234-123456789012",
                "--api-key", "sk-test-key",
            ])

            assert result.exit_code == 0
            assert "Created" in result.stdout or "new-agent" in result.stdout

    def test_config_show(self, cli_runner: CliRunner, sample_config: Path) -> None:
        """Test config show command."""
        with patch("thenvoi_cli.commands.config.ConfigManager") as MockManager:
            MockManager.return_value.get_agent_details.return_value = {
                "agent_id": "12345678-1234-1234-1234-123456789012",
                "api_key": "sk-test-key-12345",
            }

            result = cli_runner.invoke(app, ["config", "show", "test-agent"])

            assert result.exit_code == 0
            assert "12345678" in result.stdout
            # API key should be masked
            assert "sk-test-key-12345" not in result.stdout

    def test_config_show_reveal(self, cli_runner: CliRunner, sample_config: Path) -> None:
        """Test config show with --reveal."""
        with patch("thenvoi_cli.commands.config.ConfigManager") as MockManager:
            MockManager.return_value.get_agent_details.return_value = {
                "agent_id": "12345678-1234-1234-1234-123456789012",
                "api_key": "sk-test-key-12345",
            }

            result = cli_runner.invoke(app, ["config", "show", "test-agent", "--reveal"])

            assert result.exit_code == 0
            assert "sk-test-key-12345" in result.stdout

    def test_config_delete_with_confirm(
        self, cli_runner: CliRunner, sample_config: Path
    ) -> None:
        """Test config delete with confirmation."""
        with patch("thenvoi_cli.commands.config.ConfigManager") as MockManager:
            MockManager.return_value.list_agents.return_value = ["test-agent"]
            MockManager.return_value.delete_agent.return_value = True

            result = cli_runner.invoke(
                app, ["config", "delete", "test-agent", "--force"]
            )

            assert result.exit_code == 0
            assert "Deleted" in result.stdout

    def test_config_validate(self, cli_runner: CliRunner, sample_config: Path) -> None:
        """Test config validate command."""
        with patch("thenvoi_cli.commands.config.ConfigManager") as MockManager:
            MockManager.return_value.validate_config.return_value = []
            MockManager.return_value.check_permissions.return_value = True

            result = cli_runner.invoke(app, ["config", "validate"])

            assert result.exit_code == 0
            assert "valid" in result.stdout.lower()


class TestStatusCommands:
    """Tests for status and stop commands."""

    def test_status_no_agents(self, cli_runner: CliRunner) -> None:
        """Test status with no running agents."""
        with patch("thenvoi_cli.commands.status.process_manager") as mock_pm:
            mock_pm.list_running_agents.return_value = []

            result = cli_runner.invoke(app, ["status"])

            assert result.exit_code == 0
            assert "No agents running" in result.stdout

    def test_stop_not_running(self, cli_runner: CliRunner) -> None:
        """Test stopping an agent that's not running."""
        with patch("thenvoi_cli.commands.status.process_manager") as mock_pm:
            mock_pm.is_running.return_value = False

            result = cli_runner.invoke(app, ["stop", "my-agent"])

            assert result.exit_code == 1
            assert "not running" in result.stdout


class TestAdaptersCommands:
    """Tests for adapters subcommands."""

    def test_adapters_list(self, cli_runner: CliRunner) -> None:
        """Test adapters list command."""
        result = cli_runner.invoke(app, ["adapters", "list"])

        assert result.exit_code == 0
        assert "langgraph" in result.stdout.lower()
        assert "anthropic" in result.stdout.lower()

    def test_adapters_info(self, cli_runner: CliRunner) -> None:
        """Test adapters info command."""
        result = cli_runner.invoke(app, ["adapters", "info", "langgraph"])

        assert result.exit_code == 0
        assert "langgraph" in result.stdout.lower()
        assert "gpt-4o" in result.stdout

    def test_adapters_info_unknown(self, cli_runner: CliRunner) -> None:
        """Test adapters info for unknown adapter."""
        result = cli_runner.invoke(app, ["adapters", "info", "unknown-adapter"])

        assert result.exit_code == 1
        assert "Unknown adapter" in result.stdout
