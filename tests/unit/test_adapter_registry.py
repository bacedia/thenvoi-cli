"""Tests for AdapterRegistry."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from thenvoi_cli.adapter_registry import ADAPTERS, AdapterRegistry, _is_package_installed
from thenvoi_cli.exceptions import MissingDependencyError


class TestAdapterRegistry:
    """Tests for AdapterRegistry class."""

    def test_list_adapters(self) -> None:
        """Test listing all adapters."""
        registry = AdapterRegistry()
        adapters = registry.list_adapters()

        assert "langgraph" in adapters
        assert "anthropic" in adapters
        assert "claude-sdk" in adapters
        assert len(adapters) == len(ADAPTERS)

    def test_get_adapter_info(self) -> None:
        """Test getting adapter info."""
        registry = AdapterRegistry()

        info = registry.get_adapter_info("langgraph")
        assert info is not None
        assert info.name == "langgraph"
        assert info.class_name == "LangGraphAdapter"
        assert "langgraph" in info.required_deps
        assert info.default_model == "gpt-4o"

    def test_get_adapter_info_unknown(self) -> None:
        """Test getting info for unknown adapter."""
        registry = AdapterRegistry()
        info = registry.get_adapter_info("unknown-adapter")
        assert info is None

    def test_is_available_true(self) -> None:
        """Test availability check when deps are installed."""
        registry = AdapterRegistry()

        with patch.object(registry, "get_missing_deps", return_value=[]):
            assert registry.is_available("langgraph") is True

    def test_is_available_false(self) -> None:
        """Test availability check when deps are missing."""
        registry = AdapterRegistry()

        with patch.object(registry, "get_missing_deps", return_value=["langgraph"]):
            assert registry.is_available("langgraph") is False

    def test_is_available_unknown(self) -> None:
        """Test availability check for unknown adapter."""
        registry = AdapterRegistry()
        assert registry.is_available("unknown") is False

    def test_get_missing_deps(self) -> None:
        """Test getting missing dependencies."""
        registry = AdapterRegistry()

        # Mock some packages as not installed
        with patch(
            "thenvoi_cli.adapter_registry._is_package_installed",
            side_effect=lambda p: p != "langgraph",
        ):
            missing = registry.get_missing_deps("langgraph")
            assert "langgraph" in missing

    def test_get_missing_deps_unknown(self) -> None:
        """Test getting missing deps for unknown adapter."""
        registry = AdapterRegistry()
        missing = registry.get_missing_deps("unknown")
        assert missing == []

    def test_get_adapter_class_missing_deps(self) -> None:
        """Test getting adapter class when deps are missing."""
        registry = AdapterRegistry()

        with patch.object(registry, "get_missing_deps", return_value=["langgraph"]):
            with pytest.raises(MissingDependencyError) as exc_info:
                registry.get_adapter_class("langgraph")

            assert exc_info.value.adapter_name == "langgraph"
            assert "langgraph" in exc_info.value.dependencies

    def test_get_adapter_class_unknown(self) -> None:
        """Test getting class for unknown adapter."""
        registry = AdapterRegistry()

        with pytest.raises(ValueError) as exc_info:
            registry.get_adapter_class("unknown-adapter")

        assert "unknown-adapter" in str(exc_info.value)
        assert "Available" in str(exc_info.value)

    def test_get_default_model(self) -> None:
        """Test getting default model."""
        registry = AdapterRegistry()

        assert registry.get_default_model("langgraph") == "gpt-4o"
        assert registry.get_default_model("anthropic") == "claude-sonnet-4-5-20250929"
        assert registry.get_default_model("unknown") is None

    def test_get_required_env_vars(self) -> None:
        """Test getting required environment variables."""
        registry = AdapterRegistry()

        vars = registry.get_required_env_vars("langgraph")
        assert "OPENAI_API_KEY" in vars

        vars = registry.get_required_env_vars("anthropic")
        assert "ANTHROPIC_API_KEY" in vars

        vars = registry.get_required_env_vars("unknown")
        assert vars == []

    def test_is_package_installed(self) -> None:
        """Test package installation check."""
        # Standard library should be installed
        assert _is_package_installed("os") is True
        assert _is_package_installed("sys") is True

        # Non-existent package
        assert _is_package_installed("nonexistent_package_xyz_123") is False

    def test_all_adapters_have_required_fields(self) -> None:
        """Test that all adapters have required fields."""
        for name, info in ADAPTERS.items():
            assert info.name == name
            assert info.class_name
            assert info.module
            assert info.description
            assert isinstance(info.required_deps, list)
            assert isinstance(info.env_vars, list)
