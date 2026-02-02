"""Tests for ConfigManager."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from thenvoi_cli.config_manager import ConfigManager
from thenvoi_cli.exceptions import AgentNotFoundError, InvalidConfigError


class TestConfigManager:
    """Tests for ConfigManager class."""

    def test_load_agent_success(self, sample_config: Path) -> None:
        """Test loading an existing agent."""
        manager = ConfigManager(config_path=sample_config)
        agent_id, api_key = manager.load_agent("test-agent")

        assert agent_id == "12345678-1234-1234-1234-123456789012"
        assert api_key == "sk-test-api-key-12345"

    def test_load_agent_not_found(self, sample_config: Path) -> None:
        """Test loading a non-existent agent."""
        manager = ConfigManager(config_path=sample_config)

        with pytest.raises(AgentNotFoundError) as exc_info:
            manager.load_agent("nonexistent-agent")

        assert "nonexistent-agent" in str(exc_info.value)

    def test_load_agent_from_env(
        self, sample_config: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test environment variable override."""
        monkeypatch.setenv("THENVOI_AGENT_ID", "env-agent-id")
        monkeypatch.setenv("THENVOI_API_KEY", "env-api-key")

        manager = ConfigManager(config_path=sample_config)
        agent_id, api_key = manager.load_agent("any-name")

        assert agent_id == "env-agent-id"
        assert api_key == "env-api-key"

    def test_save_agent_new(self, temp_config: Path) -> None:
        """Test saving a new agent."""
        manager = ConfigManager(config_path=temp_config)
        is_new = manager.save_agent(
            "new-agent",
            "12345678-1234-1234-1234-123456789012",
            "sk-new-key",
        )

        assert is_new is True
        assert temp_config.exists()

        # Verify the content
        config = yaml.safe_load(temp_config.read_text())
        assert "new-agent" in config
        assert config["new-agent"]["agent_id"] == "12345678-1234-1234-1234-123456789012"

    def test_save_agent_invalid_uuid(self, temp_config: Path) -> None:
        """Test saving with invalid UUID."""
        manager = ConfigManager(config_path=temp_config)

        with pytest.raises(InvalidConfigError) as exc_info:
            manager.save_agent("agent", "not-a-uuid", "sk-key")

        assert "UUID" in str(exc_info.value)

    def test_save_agent_update(self, sample_config: Path) -> None:
        """Test updating an existing agent."""
        manager = ConfigManager(config_path=sample_config)
        is_new = manager.save_agent(
            "test-agent",
            "00000000-0000-0000-0000-000000000000",
            "sk-updated-key",
            force=True,
        )

        assert is_new is False

        # Verify the update
        agent_id, api_key = manager.load_agent("test-agent")
        assert agent_id == "00000000-0000-0000-0000-000000000000"
        assert api_key == "sk-updated-key"

    def test_delete_agent(self, sample_config: Path) -> None:
        """Test deleting an agent."""
        manager = ConfigManager(config_path=sample_config)

        # Verify agent exists
        assert "test-agent" in manager.list_agents()

        # Delete
        result = manager.delete_agent("test-agent")
        assert result is True
        assert "test-agent" not in manager.list_agents()

    def test_delete_agent_not_found(self, sample_config: Path) -> None:
        """Test deleting a non-existent agent."""
        manager = ConfigManager(config_path=sample_config)
        result = manager.delete_agent("nonexistent")
        assert result is False

    def test_list_agents(self, sample_config: Path) -> None:
        """Test listing all agents."""
        manager = ConfigManager(config_path=sample_config)
        agents = manager.list_agents()

        assert "test-agent" in agents
        assert "another-agent" in agents
        assert len(agents) == 2

    def test_list_agents_empty(self, temp_config: Path) -> None:
        """Test listing when no agents configured."""
        manager = ConfigManager(config_path=temp_config)
        agents = manager.list_agents()
        assert agents == []

    def test_validate_config_valid(self, sample_config: Path) -> None:
        """Test validation with valid config."""
        manager = ConfigManager(config_path=sample_config)
        errors = manager.validate_config()
        assert errors == []

    def test_validate_config_invalid_uuid(self, temp_config: Path) -> None:
        """Test validation with invalid UUID."""
        config = {
            "bad-agent": {
                "agent_id": "not-a-valid-uuid",
                "api_key": "sk-key",
            }
        }
        temp_config.write_text(yaml.dump(config))

        manager = ConfigManager(config_path=temp_config)
        errors = manager.validate_config()

        assert len(errors) == 1
        assert "UUID" in errors[0]

    def test_validate_config_missing_fields(self, temp_config: Path) -> None:
        """Test validation with missing required fields."""
        config = {
            "incomplete-agent": {
                "agent_id": "12345678-1234-1234-1234-123456789012",
                # missing api_key
            }
        }
        temp_config.write_text(yaml.dump(config))

        manager = ConfigManager(config_path=temp_config)
        errors = manager.validate_config()

        assert len(errors) == 1
        assert "api_key" in errors[0]

    def test_get_agent_details(self, sample_config: Path) -> None:
        """Test getting full agent details."""
        manager = ConfigManager(config_path=sample_config)
        details = manager.get_agent_details("test-agent")

        assert details["agent_id"] == "12345678-1234-1234-1234-123456789012"
        assert details["api_key"] == "sk-test-api-key-12345"

    def test_config_exists(self, temp_config: Path, sample_config: Path) -> None:
        """Test checking if config exists."""
        # With content
        manager = ConfigManager(config_path=sample_config)
        assert manager.config_exists() is True

        # Empty path (doesn't exist yet)
        manager2 = ConfigManager(config_path=temp_config.parent / "nonexistent.yaml")
        assert manager2.config_exists() is False

    def test_check_permissions(self, sample_config: Path) -> None:
        """Test permission checking."""
        import os
        import stat

        manager = ConfigManager(config_path=sample_config)

        # Set secure permissions
        os.chmod(sample_config, stat.S_IRUSR | stat.S_IWUSR)
        assert manager.check_permissions() is True

        # Set insecure permissions
        os.chmod(sample_config, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)
        assert manager.check_permissions() is False

    def test_uuid_validation(self, temp_config: Path) -> None:
        """Test UUID validation."""
        manager = ConfigManager(config_path=temp_config)

        # Valid UUIDs
        assert manager._validate_uuid("12345678-1234-1234-1234-123456789012") is True
        assert manager._validate_uuid("ABCDEF12-3456-7890-ABCD-EF1234567890") is True

        # Invalid UUIDs
        assert manager._validate_uuid("not-a-uuid") is False
        assert manager._validate_uuid("12345678-1234-1234-1234") is False
        assert manager._validate_uuid("") is False
