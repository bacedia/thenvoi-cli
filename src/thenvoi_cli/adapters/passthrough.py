"""Passthrough adapter for message listening without LLM processing."""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from thenvoi.core.protocols import AgentToolsProtocol
    from thenvoi.core.types import AgentInput, PlatformMessage


class PassthroughAdapter:
    """
    Adapter that outputs messages to stdout without LLM processing.

    Useful for:
    - Orchestration systems that listen for messages and trigger external actions
    - Piping messages to external scripts for processing
    - Debugging and monitoring message flow

    Example:
        thenvoi-cli run my-agent --adapter passthrough
        thenvoi-cli run my-agent --adapter passthrough | ./process-messages.py

    Output format (JSON, one per line):
        {"room_id": "...", "sender": "...", "content": "...", ...}
    """

    def __init__(self, output_format: str = "json") -> None:
        """
        Initialize the passthrough adapter.

        Args:
            output_format: Output format ("json" or "plain"). Defaults to "json".
        """
        self.output_format = output_format
        self.agent_name: str = ""
        self.agent_description: str = ""

    async def on_event(self, inp: "AgentInput") -> None:
        """
        Process incoming message by outputting to stdout.

        Args:
            inp: AgentInput containing the message and context.
        """
        self._output_message(inp.msg, inp.room_id)

    async def on_message(
        self,
        msg: "PlatformMessage",
        tools: "AgentToolsProtocol",
        history: Any,
        participants_msg: str | None,
        *,
        is_session_bootstrap: bool,
        room_id: str,
    ) -> None:
        """
        Handle incoming message by outputting to stdout.

        This method is called by SimpleAdapter-style wrappers.

        Args:
            msg: The platform message.
            tools: Agent tools (unused - no responses sent).
            history: Message history (unused).
            participants_msg: Participant update message (unused).
            is_session_bootstrap: Whether this is the first message in session.
            room_id: The room identifier.
        """
        self._output_message(msg, room_id)

    def _output_message(self, msg: "PlatformMessage", room_id: str) -> None:
        """Output a message to stdout."""
        if self.output_format == "json":
            output = {
                "id": msg.id,
                "room_id": room_id,
                "sender_id": msg.sender_id,
                "sender_name": msg.sender_name,
                "sender_type": msg.sender_type,
                "content": msg.content,
                "message_type": msg.message_type,
                "timestamp": msg.created_at.isoformat(),
            }
            print(json.dumps(output), file=sys.stdout, flush=True)
        else:
            # Plain text format
            sender = msg.sender_name or msg.sender_type or "Unknown"
            print(f"[{room_id}] {sender}: {msg.content}", file=sys.stdout, flush=True)

    async def on_cleanup(self, room_id: str) -> None:
        """Clean up when leaving a room (no-op for passthrough)."""
        pass

    async def on_started(self, agent_name: str, agent_description: str) -> None:
        """Called after agent starts."""
        self.agent_name = agent_name
        self.agent_description = agent_description
