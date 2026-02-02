"""Tests for output formatting."""

from __future__ import annotations

import json
import os
from unittest.mock import patch

import pytest

from thenvoi_cli.output import (
    OutputFormat,
    OutputFormatter,
    mask_api_key,
    mask_uuid,
)


class TestOutputFormatter:
    """Tests for OutputFormatter class."""

    def test_format_dict_json(self) -> None:
        """Test formatting dict as JSON."""
        formatter = OutputFormatter()
        data = {"key": "value", "number": 42}

        result = formatter.format_dict(data, OutputFormat.JSON)
        parsed = json.loads(result)

        assert parsed["key"] == "value"
        assert parsed["number"] == 42

    def test_format_dict_plain(self) -> None:
        """Test formatting dict as plain text."""
        formatter = OutputFormatter()
        data = {"key": "value", "number": 42}

        result = formatter.format_dict(data, OutputFormat.PLAIN)

        assert "key: value" in result
        assert "number: 42" in result

    def test_format_list_json(self) -> None:
        """Test formatting list as JSON."""
        formatter = OutputFormatter()
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]

        result = formatter.format_list(data, OutputFormat.JSON)
        parsed = json.loads(result)

        assert len(parsed) == 2
        assert parsed[0]["name"] == "Alice"

    def test_format_list_plain(self) -> None:
        """Test formatting list as plain text."""
        formatter = OutputFormatter()
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]

        result = formatter.format_list(data, OutputFormat.PLAIN, headers=["name", "age"])

        assert "Alice" in result
        assert "Bob" in result

    def test_format_list_empty(self) -> None:
        """Test formatting empty list."""
        formatter = OutputFormatter()

        result = formatter.format_list([], OutputFormat.JSON)
        assert result == "[]"

        result = formatter.format_list([], OutputFormat.PLAIN)
        assert result == "No results"


class TestMaskFunctions:
    """Tests for masking functions."""

    def test_mask_api_key_normal(self) -> None:
        """Test masking a normal API key."""
        key = "sk-test-api-key-12345678901234567890"
        masked = mask_api_key(key)

        assert masked.endswith("7890")
        assert key[:10] not in masked
        assert "*" in masked

    def test_mask_api_key_short(self) -> None:
        """Test masking a short key."""
        key = "short"
        masked = mask_api_key(key)

        assert masked == "****"

    def test_mask_api_key_edge(self) -> None:
        """Test masking edge case lengths."""
        assert mask_api_key("12345678") == "****"  # Exactly 8
        assert mask_api_key("123456789").endswith("6789")  # 9 chars

    def test_mask_uuid_valid(self) -> None:
        """Test masking a valid UUID."""
        uuid = "12345678-1234-1234-1234-123456789012"
        masked = mask_uuid(uuid)

        assert masked.startswith("12345678")
        assert masked.endswith("123456789012")
        assert "****" in masked

    def test_mask_uuid_invalid(self) -> None:
        """Test masking an invalid UUID format."""
        invalid = "not-a-uuid"
        masked = mask_uuid(invalid)

        # Should return unchanged
        assert masked == invalid


class TestOutputFormatEnum:
    """Tests for OutputFormat enum."""

    def test_enum_values(self) -> None:
        """Test enum string values."""
        assert OutputFormat.JSON.value == "json"
        assert OutputFormat.TABLE.value == "table"
        assert OutputFormat.PLAIN.value == "plain"

    def test_enum_from_string(self) -> None:
        """Test creating enum from string."""
        assert OutputFormat("json") == OutputFormat.JSON
        assert OutputFormat("table") == OutputFormat.TABLE
        assert OutputFormat("plain") == OutputFormat.PLAIN
