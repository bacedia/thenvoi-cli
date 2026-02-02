"""SDK client wrapper for CLI operations."""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, AsyncIterator

from thenvoi_cli.config_manager import ConfigManager
from thenvoi_cli.exceptions import ConnectionError, MissingEnvironmentError

if TYPE_CHECKING:
    from thenvoi.platform.link import ThenvoiLink
    from thenvoi.runtime.tools import AgentTools


class SDKClient:
    """Simplified SDK client for CLI operations.

    Provides a clean interface for CLI commands to interact with the
    Thenvoi platform without managing low-level connection details.
    """

    def __init__(
        self,
        agent_id: str,
        api_key: str,
        ws_url: str | None = None,
        rest_url: str | None = None,
    ) -> None:
        """Initialize the SDK client.

        Args:
            agent_id: The agent UUID.
            api_key: The agent API key.
            ws_url: WebSocket URL (uses THENVOI_WS_URL if not provided).
            rest_url: REST API URL (uses THENVOI_REST_URL if not provided).
        """
        self.agent_id = agent_id
        self.api_key = api_key
        self.ws_url = ws_url or os.getenv("THENVOI_WS_URL")
        self.rest_url = rest_url or os.getenv("THENVOI_REST_URL")
        self._link: ThenvoiLink | None = None

    def _validate_urls(self) -> None:
        """Validate that required URLs are configured."""
        if not self.ws_url:
            raise MissingEnvironmentError("THENVOI_WS_URL")
        if not self.rest_url:
            raise MissingEnvironmentError("THENVOI_REST_URL")

    async def connect(self) -> None:
        """Establish connection to the Thenvoi platform."""
        self._validate_urls()

        try:
            from thenvoi.platform.link import ThenvoiLink

            self._link = ThenvoiLink(
                agent_id=self.agent_id,
                api_key=self.api_key,
                ws_url=self.ws_url,
                rest_url=self.rest_url,
            )
            await self._link.connect()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Thenvoi platform: {e}") from e

    async def disconnect(self) -> None:
        """Close the connection."""
        if self._link:
            try:
                await self._link.disconnect()
            except Exception:
                pass  # Ignore disconnect errors
            finally:
                self._link = None

    @property
    def is_connected(self) -> bool:
        """Check if the client is connected."""
        return self._link is not None

    def get_tools(self, room_id: str = "") -> AgentTools:
        """Get AgentTools instance bound to a room.

        Args:
            room_id: Room ID to bind tools to. Required for most operations
                except create_chatroom and lookup_peers.

        Returns:
            AgentTools instance.

        Raises:
            ConnectionError: If not connected.
        """
        if not self._link:
            raise ConnectionError("Not connected to Thenvoi platform")

        from thenvoi.runtime.tools import AgentTools

        # AgentTools needs the REST client from the link, not the link itself
        return AgentTools(
            room_id=room_id,
            rest=self._link.rest,
        )

    async def get_rooms(self) -> list[dict[str, Any]]:
        """Get list of rooms the agent has access to.

        Returns:
            List of room dictionaries.
        """
        if not self._link:
            raise ConnectionError("Not connected to Thenvoi platform")

        response = await self._link.rest.agent_api.list_agent_chats()
        if not response.data:
            return []

        return [
            {
                "id": chat.id,
                "name": getattr(chat, "name", ""),
                "participant_count": getattr(chat, "participant_count", 0),
            }
            for chat in response.data
        ]

    async def health_check(self) -> dict[str, Any]:
        """Perform a health check against the platform.

        Returns:
            Health check response.
        """
        self._validate_urls()

        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.rest_url}/health",
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]


@asynccontextmanager
async def create_sdk_client(
    agent_name: str,
    config_manager: ConfigManager | None = None,
) -> AsyncIterator[SDKClient]:
    """Create and connect an SDK client from configuration.

    Args:
        agent_name: The agent name in configuration.
        config_manager: Optional ConfigManager instance.

    Yields:
        Connected SDKClient instance.
    """
    config = config_manager or ConfigManager()
    agent_id, api_key = config.load_agent(agent_name)

    client = SDKClient(agent_id=agent_id, api_key=api_key)
    await client.connect()
    try:
        yield client
    finally:
        await client.disconnect()


def run_async(coro: Any) -> Any:
    """Run an async coroutine synchronously.

    This is a helper for CLI commands that need to call async SDK methods.

    Args:
        coro: The coroutine to run.

    Returns:
        The coroutine result.
    """
    return asyncio.run(coro)
