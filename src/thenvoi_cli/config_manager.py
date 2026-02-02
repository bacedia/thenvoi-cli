"""Configuration management for thenvoi-cli."""

from __future__ import annotations

import os
import re
import stat
from pathlib import Path
from typing import Any

import yaml

from thenvoi_cli.exceptions import AgentNotFoundError, InvalidConfigError


class ConfigManager:
    """Manages agent configuration storage and retrieval."""

    DEFAULT_CONFIG_PATH = Path("agent_config.yaml")
    ENV_CONFIG_PATH = "THENVOI_CONFIG_PATH"

    # UUID regex pattern
    UUID_PATTERN = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize the configuration manager.

        Args:
            config_path: Path to the configuration file. If not provided,
                uses THENVOI_CONFIG_PATH env var or defaults to agent_config.yaml.
        """
        if config_path:
            self.config_path = config_path
        elif os.getenv(self.ENV_CONFIG_PATH):
            self.config_path = Path(os.environ[self.ENV_CONFIG_PATH])
        else:
            self.config_path = self.DEFAULT_CONFIG_PATH

    def _load_config(self) -> dict[str, Any]:
        """Load the configuration file."""
        if not self.config_path.exists():
            return {}
        with open(self.config_path) as f:
            data = yaml.safe_load(f)
            return data if data else {}

    def _save_config(self, config: dict[str, Any]) -> None:
        """Save the configuration file with secure permissions."""
        # Create parent directories if needed
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        with open(self.config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        # Set restrictive permissions (owner read/write only)
        os.chmod(self.config_path, stat.S_IRUSR | stat.S_IWUSR)

    def _validate_uuid(self, value: str) -> bool:
        """Validate that a string is a valid UUID."""
        return bool(self.UUID_PATTERN.match(value))

    def load_agent(self, name: str) -> tuple[str, str]:
        """Load agent credentials from configuration.

        Environment variables take precedence:
        - THENVOI_AGENT_ID overrides agent_id
        - THENVOI_API_KEY overrides api_key

        Args:
            name: The agent name in the configuration.

        Returns:
            Tuple of (agent_id, api_key).

        Raises:
            AgentNotFoundError: If the agent is not found in configuration.
            InvalidConfigError: If the configuration is invalid.
        """
        # Check for environment variable overrides
        env_agent_id = os.getenv("THENVOI_AGENT_ID")
        env_api_key = os.getenv("THENVOI_API_KEY")

        if env_agent_id and env_api_key:
            return env_agent_id, env_api_key

        # Load from config file
        config = self._load_config()

        if name not in config:
            raise AgentNotFoundError(name)

        agent_config = config[name]

        if not isinstance(agent_config, dict):
            raise InvalidConfigError(f"Invalid configuration for agent '{name}'")

        agent_id = env_agent_id or agent_config.get("agent_id")
        api_key = env_api_key or agent_config.get("api_key")

        if not agent_id:
            raise InvalidConfigError(f"Missing 'agent_id' for agent '{name}'")
        if not api_key:
            raise InvalidConfigError(f"Missing 'api_key' for agent '{name}'")

        return str(agent_id), str(api_key)

    def save_agent(
        self,
        name: str,
        agent_id: str,
        api_key: str,
        *,
        force: bool = False,
    ) -> bool:
        """Save agent credentials to configuration.

        Args:
            name: The agent name.
            agent_id: The agent UUID from the Thenvoi platform.
            api_key: The agent API key.
            force: If True, overwrite existing agent without warning.

        Returns:
            True if a new agent was created, False if existing was updated.

        Raises:
            InvalidConfigError: If the agent_id is not a valid UUID.
        """
        if not self._validate_uuid(agent_id):
            raise InvalidConfigError(
                f"Invalid agent_id '{agent_id}': must be a valid UUID"
            )

        config = self._load_config()
        is_new = name not in config

        config[name] = {
            "agent_id": agent_id,
            "api_key": api_key,
        }

        self._save_config(config)
        return is_new

    def delete_agent(self, name: str) -> bool:
        """Delete an agent from configuration.

        Args:
            name: The agent name to delete.

        Returns:
            True if the agent was deleted, False if it didn't exist.
        """
        config = self._load_config()

        if name not in config:
            return False

        del config[name]
        self._save_config(config)
        return True

    def list_agents(self) -> list[str]:
        """List all configured agent names.

        Returns:
            List of agent names.
        """
        config = self._load_config()
        return list(config.keys())

    def get_agent_details(self, name: str) -> dict[str, Any]:
        """Get full details for an agent.

        Args:
            name: The agent name.

        Returns:
            Dictionary with agent configuration.

        Raises:
            AgentNotFoundError: If the agent is not found.
        """
        config = self._load_config()

        if name not in config:
            raise AgentNotFoundError(name)

        return dict(config[name])

    def validate_config(self, name: str | None = None) -> list[str]:
        """Validate configuration and return list of errors.

        Args:
            name: Specific agent to validate, or None for all.

        Returns:
            List of validation error messages. Empty if valid.
        """
        errors: list[str] = []
        config = self._load_config()

        agents_to_check = [name] if name else list(config.keys())

        for agent_name in agents_to_check:
            if agent_name not in config:
                errors.append(f"Agent '{agent_name}' not found in configuration")
                continue

            agent_config = config[agent_name]

            if not isinstance(agent_config, dict):
                errors.append(f"Agent '{agent_name}': configuration is not a dictionary")
                continue

            agent_id = agent_config.get("agent_id")
            api_key = agent_config.get("api_key")

            if not agent_id:
                errors.append(f"Agent '{agent_name}': missing 'agent_id'")
            elif not self._validate_uuid(str(agent_id)):
                errors.append(f"Agent '{agent_name}': invalid UUID format for 'agent_id'")

            if not api_key:
                errors.append(f"Agent '{agent_name}': missing 'api_key'")

        return errors

    def config_exists(self) -> bool:
        """Check if the configuration file exists."""
        return self.config_path.exists()

    def check_permissions(self) -> bool:
        """Check if config file has secure permissions.

        Returns:
            True if permissions are secure (owner-only), False otherwise.
        """
        if not self.config_path.exists():
            return True

        mode = self.config_path.stat().st_mode
        # Check if group or others have any permissions
        insecure = mode & (stat.S_IRWXG | stat.S_IRWXO)
        return not insecure

    def get_platform_urls(self) -> tuple[str | None, str | None]:
        """Get platform URLs from environment variables.

        Returns:
            Tuple of (rest_url, ws_url), either may be None if not set.
        """
        rest_url = os.getenv("THENVOI_REST_URL")
        ws_url = os.getenv("THENVOI_WS_URL")
        return rest_url, ws_url
