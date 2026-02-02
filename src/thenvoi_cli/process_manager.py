"""Process management for background agents."""

from __future__ import annotations

import os
import signal
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass
class AgentProcess:
    """Information about a running agent process."""

    name: str
    pid: int
    started_at: datetime
    adapter: str | None = None


class ProcessManager:
    """Manages background agent processes."""

    STATE_DIR = Path.home() / ".local" / "state" / "thenvoi-cli"

    def __init__(self, state_dir: Path | None = None) -> None:
        """Initialize the process manager.

        Args:
            state_dir: Directory for storing PID files.
        """
        self.state_dir = state_dir or self.STATE_DIR
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _get_pid_file(self, agent_name: str) -> Path:
        """Get the PID file path for an agent."""
        return self.state_dir / f"{agent_name}.pid"

    def _get_info_file(self, agent_name: str) -> Path:
        """Get the info file path for an agent."""
        return self.state_dir / f"{agent_name}.info"

    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with the given PID is running."""
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def register_agent(
        self,
        agent_name: str,
        pid: int,
        adapter: str | None = None,
    ) -> None:
        """Register a running agent.

        Args:
            agent_name: The agent name.
            pid: The process ID.
            adapter: The adapter being used.
        """
        pid_file = self._get_pid_file(agent_name)
        pid_file.write_text(str(pid))

        info_file = self._get_info_file(agent_name)
        info = {
            "started_at": datetime.now().isoformat(),
            "adapter": adapter,
        }
        import json

        info_file.write_text(json.dumps(info))

    def unregister_agent(self, agent_name: str) -> None:
        """Unregister an agent.

        Args:
            agent_name: The agent name.
        """
        pid_file = self._get_pid_file(agent_name)
        info_file = self._get_info_file(agent_name)

        if pid_file.exists():
            pid_file.unlink()
        if info_file.exists():
            info_file.unlink()

    def get_pid(self, agent_name: str) -> int | None:
        """Get the PID for a running agent.

        Args:
            agent_name: The agent name.

        Returns:
            The PID or None if not running.
        """
        pid_file = self._get_pid_file(agent_name)
        if not pid_file.exists():
            return None

        try:
            pid = int(pid_file.read_text().strip())
            if self._is_process_running(pid):
                return pid
            else:
                # Clean up stale PID file
                self.unregister_agent(agent_name)
                return None
        except (ValueError, OSError):
            return None

    def is_running(self, agent_name: str) -> bool:
        """Check if an agent is running.

        Args:
            agent_name: The agent name.

        Returns:
            True if the agent is running.
        """
        return self.get_pid(agent_name) is not None

    def get_agent_status(self, agent_name: str) -> AgentProcess | None:
        """Get status information for an agent.

        Args:
            agent_name: The agent name.

        Returns:
            AgentProcess or None if not running.
        """
        pid = self.get_pid(agent_name)
        if pid is None:
            return None

        info_file = self._get_info_file(agent_name)
        adapter = None
        started_at = datetime.now()

        if info_file.exists():
            try:
                import json

                info = json.loads(info_file.read_text())
                adapter = info.get("adapter")
                if "started_at" in info:
                    started_at = datetime.fromisoformat(info["started_at"])
            except (json.JSONDecodeError, ValueError):
                pass

        return AgentProcess(
            name=agent_name,
            pid=pid,
            started_at=started_at,
            adapter=adapter,
        )

    def list_running_agents(self) -> list[AgentProcess]:
        """List all running agents.

        Returns:
            List of AgentProcess for running agents.
        """
        agents: list[AgentProcess] = []

        for pid_file in self.state_dir.glob("*.pid"):
            agent_name = pid_file.stem
            status = self.get_agent_status(agent_name)
            if status:
                agents.append(status)

        return agents

    def stop_agent(
        self,
        agent_name: str,
        force: bool = False,
        timeout: int = 30,
    ) -> bool:
        """Stop a running agent.

        Args:
            agent_name: The agent name.
            force: If True, use SIGKILL instead of SIGTERM.
            timeout: Seconds to wait before force killing (if not force).

        Returns:
            True if the agent was stopped.
        """
        pid = self.get_pid(agent_name)
        if pid is None:
            return False

        try:
            if force:
                os.kill(pid, signal.SIGKILL)
            else:
                os.kill(pid, signal.SIGTERM)

                # Wait for graceful shutdown
                import time

                for _ in range(timeout):
                    if not self._is_process_running(pid):
                        break
                    time.sleep(1)
                else:
                    # Force kill after timeout
                    os.kill(pid, signal.SIGKILL)

            self.unregister_agent(agent_name)
            return True

        except OSError:
            # Process already gone
            self.unregister_agent(agent_name)
            return True

    def stop_all(self, force: bool = False) -> int:
        """Stop all running agents.

        Args:
            force: If True, use SIGKILL.

        Returns:
            Number of agents stopped.
        """
        count = 0
        for agent in self.list_running_agents():
            if self.stop_agent(agent.name, force=force):
                count += 1
        return count


# Global process manager instance
process_manager = ProcessManager()
