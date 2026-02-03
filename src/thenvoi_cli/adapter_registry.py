"""Adapter registry for framework selection."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from thenvoi_cli.exceptions import MissingDependencyError

if TYPE_CHECKING:
    pass


@dataclass
class AdapterInfo:
    """Information about an adapter."""

    name: str
    class_name: str
    module: str
    description: str
    required_deps: list[str]
    default_model: str | None
    env_vars: list[str]


# Registry of all available adapters
ADAPTERS: dict[str, AdapterInfo] = {
    "langgraph": AdapterInfo(
        name="langgraph",
        class_name="LangGraphAdapter",
        module="thenvoi.adapters.langgraph",
        description="LangGraph ReAct agent with tool support",
        required_deps=["langgraph", "langchain_openai"],
        default_model="gpt-4o",
        env_vars=["OPENAI_API_KEY"],
    ),
    "anthropic": AdapterInfo(
        name="anthropic",
        class_name="AnthropicAdapter",
        module="thenvoi.adapters.anthropic",
        description="Anthropic SDK with direct Claude integration",
        required_deps=["anthropic"],
        default_model="claude-sonnet-4-5-20250929",
        env_vars=["ANTHROPIC_API_KEY"],
    ),
    "pydantic-ai": AdapterInfo(
        name="pydantic-ai",
        class_name="PydanticAIAdapter",
        module="thenvoi.adapters.pydantic_ai",
        description="Pydantic AI with type-safe tools",
        required_deps=["pydantic_ai"],
        default_model="openai:gpt-4o",
        env_vars=["OPENAI_API_KEY"],
    ),
    "claude-sdk": AdapterInfo(
        name="claude-sdk",
        class_name="ClaudeSDKAdapter",
        module="thenvoi.adapters.claude_sdk",
        description="Claude Agent SDK with extended thinking",
        required_deps=["claude_agent_sdk"],
        default_model="claude-sonnet-4-5-20250929",
        env_vars=["ANTHROPIC_API_KEY"],
    ),
    "crewai": AdapterInfo(
        name="crewai",
        class_name="CrewAIAdapter",
        module="thenvoi.adapters.crewai",
        description="CrewAI role-based multi-agent framework",
        required_deps=["crewai"],
        default_model="gpt-4o",
        env_vars=["OPENAI_API_KEY"],
    ),
    "parlant": AdapterInfo(
        name="parlant",
        class_name="ParlantAdapter",
        module="thenvoi.adapters.parlant",
        description="Parlant guideline-based behavior framework",
        required_deps=["parlant"],
        default_model="gpt-4o",
        env_vars=["OPENAI_API_KEY"],
    ),
    "a2a": AdapterInfo(
        name="a2a",
        class_name="A2AAdapter",
        module="thenvoi.adapters.a2a",
        description="A2A protocol adapter for external agents",
        required_deps=["a2a_sdk"],
        default_model=None,
        env_vars=[],
    ),
    "a2a-gateway": AdapterInfo(
        name="a2a-gateway",
        class_name="A2AGatewayAdapter",
        module="thenvoi.adapters.a2a_gateway",
        description="A2A gateway to expose peers as endpoints",
        required_deps=["a2a_sdk", "starlette", "uvicorn"],
        default_model=None,
        env_vars=[],
    ),
    "passthrough": AdapterInfo(
        name="passthrough",
        class_name="PassthroughAdapter",
        module="thenvoi_cli.adapters.passthrough",
        description="Output messages to stdout without LLM processing",
        required_deps=[],
        default_model=None,
        env_vars=[],
    ),
}


def _is_package_installed(package_name: str) -> bool:
    """Check if a Python package is installed."""
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False


class AdapterRegistry:
    """Registry for discovering and loading adapters."""

    def list_adapters(self) -> list[str]:
        """List all registered adapter names."""
        return list(ADAPTERS.keys())

    def get_adapter_info(self, name: str) -> AdapterInfo | None:
        """Get information about an adapter.

        Args:
            name: The adapter name.

        Returns:
            AdapterInfo or None if not found.
        """
        return ADAPTERS.get(name)

    def is_available(self, name: str) -> bool:
        """Check if an adapter's dependencies are installed.

        Args:
            name: The adapter name.

        Returns:
            True if all dependencies are available.
        """
        info = ADAPTERS.get(name)
        if not info:
            return False

        return all(_is_package_installed(dep) for dep in info.required_deps)

    def get_missing_deps(self, name: str) -> list[str]:
        """Get list of missing dependencies for an adapter.

        Args:
            name: The adapter name.

        Returns:
            List of missing package names.
        """
        info = ADAPTERS.get(name)
        if not info:
            return []

        return [dep for dep in info.required_deps if not _is_package_installed(dep)]

    def get_adapter_class(self, name: str) -> type[Any]:
        """Get the adapter class, importing it lazily.

        Args:
            name: The adapter name.

        Returns:
            The adapter class.

        Raises:
            ValueError: If the adapter is not found.
            MissingDependencyError: If dependencies are not installed.
        """
        info = ADAPTERS.get(name)
        if not info:
            available = ", ".join(self.list_adapters())
            raise ValueError(f"Unknown adapter '{name}'. Available: {available}")

        missing = self.get_missing_deps(name)
        if missing:
            raise MissingDependencyError(name, missing)

        module = importlib.import_module(info.module)
        return getattr(module, info.class_name)  # type: ignore[no-any-return]

    def get_default_model(self, name: str) -> str | None:
        """Get the default model for an adapter.

        Args:
            name: The adapter name.

        Returns:
            Default model name or None.
        """
        info = ADAPTERS.get(name)
        return info.default_model if info else None

    def get_required_env_vars(self, name: str) -> list[str]:
        """Get required environment variables for an adapter.

        Args:
            name: The adapter name.

        Returns:
            List of required environment variable names.
        """
        info = ADAPTERS.get(name)
        return info.env_vars if info else []


# Global registry instance
registry = AdapterRegistry()
