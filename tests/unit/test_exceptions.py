"""Tests for custom exceptions."""

from __future__ import annotations

import pytest

from thenvoi_cli.exceptions import (
    AdapterError,
    AgentNotFoundError,
    AgentNotRunningError,
    AuthenticationError,
    ConfigurationError,
    ConnectionError,
    InvalidConfigError,
    MissingDependencyError,
    MissingEnvironmentError,
    RoomNotFoundError,
    ThenvoiCLIError,
)


class TestExceptions:
    """Tests for custom exception classes."""

    def test_base_exception(self) -> None:
        """Test base ThenvoiCLIError."""
        error = ThenvoiCLIError("Test error", hint="Test hint")

        assert error.message == "Test error"
        assert error.hint == "Test hint"
        assert error.exit_code == 1
        assert str(error) == "Test error"

    def test_agent_not_found_error(self) -> None:
        """Test AgentNotFoundError."""
        error = AgentNotFoundError("my-agent")

        assert error.agent_name == "my-agent"
        assert "my-agent" in error.message
        assert error.hint is not None
        assert "config list" in error.hint

    def test_invalid_config_error(self) -> None:
        """Test InvalidConfigError."""
        error = InvalidConfigError("Invalid UUID format")

        assert "Invalid UUID" in error.message
        assert isinstance(error, ConfigurationError)

    def test_missing_environment_error(self) -> None:
        """Test MissingEnvironmentError."""
        error = MissingEnvironmentError("THENVOI_REST_URL")

        assert error.var_name == "THENVOI_REST_URL"
        assert "THENVOI_REST_URL" in error.message
        assert "export" in error.hint

    def test_connection_error(self) -> None:
        """Test ConnectionError."""
        error = ConnectionError("Connection refused")

        assert error.exit_code == 2
        assert "Connection refused" in error.message

    def test_authentication_error(self) -> None:
        """Test AuthenticationError."""
        error = AuthenticationError()

        assert error.exit_code == 3
        assert "Authentication" in error.message
        assert error.hint is not None

    def test_missing_dependency_error(self) -> None:
        """Test MissingDependencyError."""
        error = MissingDependencyError("langgraph", ["langgraph", "langchain-openai"])

        assert error.adapter_name == "langgraph"
        assert error.dependencies == ["langgraph", "langchain-openai"]
        assert "langgraph" in error.message
        assert "pip install" in error.hint

    def test_room_not_found_error(self) -> None:
        """Test RoomNotFoundError."""
        error = RoomNotFoundError("room-123")

        assert error.room_id == "room-123"
        assert "room-123" in error.message

    def test_agent_not_running_error(self) -> None:
        """Test AgentNotRunningError."""
        error = AgentNotRunningError("my-agent")

        assert error.agent_name == "my-agent"
        assert "my-agent" in error.message
        assert "thenvoi-cli run" in error.hint

    def test_exception_hierarchy(self) -> None:
        """Test exception inheritance hierarchy."""
        assert issubclass(ConfigurationError, ThenvoiCLIError)
        assert issubclass(AgentNotFoundError, ConfigurationError)
        assert issubclass(InvalidConfigError, ConfigurationError)
        assert issubclass(MissingEnvironmentError, ConfigurationError)
        assert issubclass(ConnectionError, ThenvoiCLIError)
        assert issubclass(AuthenticationError, ThenvoiCLIError)
        assert issubclass(AdapterError, ThenvoiCLIError)
        assert issubclass(MissingDependencyError, AdapterError)
