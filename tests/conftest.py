"""Shared pytest fixtures for thenvoi-cli tests."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

if TYPE_CHECKING:
    pass


@pytest.fixture
def cli_runner() -> CliRunner:
    """Typer CLI runner for testing commands."""
    return CliRunner()


@pytest.fixture
def temp_config(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary config file path."""
    config_file = tmp_path / "agent_config.yaml"
    with patch("thenvoi_cli.config_manager.ConfigManager.DEFAULT_CONFIG_PATH", config_file):
        yield config_file


@pytest.fixture
def sample_config(temp_config: Path) -> Path:
    """Create a sample configuration file."""
    import yaml

    config = {
        "test-agent": {
            "agent_id": "12345678-1234-1234-1234-123456789012",
            "api_key": "sk-test-api-key-12345",
        },
        "another-agent": {
            "agent_id": "87654321-4321-4321-4321-210987654321",
            "api_key": "sk-another-api-key-67890",
        },
    }

    temp_config.write_text(yaml.dump(config))
    return temp_config


@pytest.fixture
def mock_agent_config() -> tuple[str, str]:
    """Return mock agent credentials."""
    return ("12345678-1234-1234-1234-123456789012", "sk-test-api-key-12345")


@pytest.fixture
def mock_env_vars() -> Generator[None, None, None]:
    """Set up mock environment variables."""
    env_vars = {
        "THENVOI_REST_URL": "https://test.thenvoi.com/",
        "THENVOI_WS_URL": "wss://test.thenvoi.com/ws",
        "OPENAI_API_KEY": "sk-test-openai-key",
        "ANTHROPIC_API_KEY": "sk-test-anthropic-key",
    }

    with patch.dict(os.environ, env_vars):
        yield


@pytest.fixture
def mock_thenvoi_link() -> Generator[MagicMock, None, None]:
    """Mock ThenvoiLink for transport layer tests."""
    with patch("thenvoi_cli.sdk_client.ThenvoiLink") as mock:
        link_instance = AsyncMock()
        link_instance.connect = AsyncMock()
        link_instance.disconnect = AsyncMock()
        link_instance.rest = MagicMock()
        link_instance.rest.get_rooms = AsyncMock(return_value=[
            {"id": "room-1", "name": "Test Room 1", "participant_count": 3},
            {"id": "room-2", "name": "Test Room 2", "participant_count": 2},
        ])
        mock.return_value = link_instance
        yield mock


@pytest.fixture
def mock_agent_tools() -> Generator[MagicMock, None, None]:
    """Mock AgentTools for platform operation tests."""
    with patch("thenvoi_cli.sdk_client.AgentTools") as mock:
        tools_instance = MagicMock()
        tools_instance.send_message = AsyncMock(return_value={"id": "msg-123"})
        tools_instance.send_event = AsyncMock(return_value={"id": "event-123"})
        tools_instance.get_participants = AsyncMock(return_value=[
            {"name": "User", "role": "member"},
            {"name": "Bot", "role": "member"},
        ])
        tools_instance.add_participant = AsyncMock(return_value={"success": True})
        tools_instance.remove_participant = AsyncMock(return_value={"success": True})
        tools_instance.create_chatroom = AsyncMock(return_value="room-new-123")
        tools_instance.lookup_peers = AsyncMock(return_value={
            "peers": [
                {"name": "Agent1", "description": "First agent", "status": "online"},
                {"name": "Agent2", "description": "Second agent", "status": "offline"},
            ],
            "total": 2,
        })
        mock.return_value = tools_instance
        yield mock


@pytest.fixture
def mock_sdk_client(mock_thenvoi_link: MagicMock, mock_agent_tools: MagicMock) -> Generator[MagicMock, None, None]:
    """Mock SDKClient combining link and tools mocks."""
    with patch("thenvoi_cli.commands.rooms.SDKClient") as mock:
        client_instance = AsyncMock()
        client_instance.connect = AsyncMock()
        client_instance.disconnect = AsyncMock()
        client_instance.get_rooms = AsyncMock(return_value=[
            {"id": "room-1", "name": "Test Room 1", "participant_count": 3},
        ])
        client_instance.get_tools = MagicMock(return_value=mock_agent_tools.return_value)
        mock.return_value = client_instance
        yield mock


@pytest.fixture
def mock_process_manager(tmp_path: Path) -> Generator[Any, None, None]:
    """Mock ProcessManager with temp state directory."""
    from thenvoi_cli.process_manager import ProcessManager

    pm = ProcessManager(state_dir=tmp_path / "state")
    with patch("thenvoi_cli.process_manager.process_manager", pm):
        yield pm


@pytest.fixture
def isolate_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate configuration to temp directory."""
    config_path = tmp_path / "agent_config.yaml"
    monkeypatch.setattr(
        "thenvoi_cli.config_manager.ConfigManager.DEFAULT_CONFIG_PATH",
        config_path,
    )
    return config_path
