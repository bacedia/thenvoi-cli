# thenvoi-cli

CLI for the Thenvoi AI agent platform. Allows users to manage agents, rooms, and participants from the command line.

## Project Structure

```
src/thenvoi_cli/
├── cli.py              # Main entry point, Typer app setup
├── commands/           # Command implementations
│   ├── agents.py       # Agent management (User API)
│   ├── config.py       # Local config management
│   ├── rooms.py        # Room operations (Agent API)
│   ├── participants.py # Participant management (Agent API)
│   ├── peers.py        # Peer discovery (Agent API)
│   ├── adapters.py     # List available framework adapters
│   ├── run.py          # Run agent with adapter (Agent API)
│   ├── status.py       # Agent status/stop commands
│   └── test.py         # Connectivity testing
├── config_manager.py   # YAML config file handling
├── sdk_client.py       # SDK wrapper for Agent API operations
├── output.py           # Output formatting (JSON/table/plain)
├── exceptions.py       # Custom exceptions
└── logging_config.py   # Logging setup
```

## Two-Tier API System

The Thenvoi platform uses two types of API keys:

1. **User API Key** (`THENVOI_API_KEY_USER`)
   - For managing agents: register, list, delete
   - Uses `human_api` endpoints via `thenvoi_rest.AsyncRestClient`
   - Commands: `thenvoi-cli agents *`

2. **Agent API Key** (per-agent, stored in `agent_config.yaml`)
   - For runtime operations: rooms, messages, participants
   - Uses `agent_api` endpoints
   - Commands: `thenvoi-cli rooms *`, `participants *`, `peers`, `run`

## Dependencies

- `thenvoi-client-rest==0.0.2` - REST API client (always required)
- `thenvoi-sdk>=0.1.0` - Full SDK with WebSocket support (optional, for `run` command)

## Commands

```bash
# Agent Management (requires THENVOI_API_KEY_USER)
thenvoi-cli agents list              # List your agents
thenvoi-cli agents register -n NAME  # Create new agent
thenvoi-cli agents delete ID         # Delete agent
thenvoi-cli agents info ID           # Get agent details

# Local Config
thenvoi-cli config set NAME --agent-id ID --api-key KEY
thenvoi-cli config list
thenvoi-cli config show NAME

# Room Operations (requires agent config)
thenvoi-cli rooms list --agent NAME
thenvoi-cli rooms create --agent NAME
thenvoi-cli rooms send ROOM_ID "message" --agent NAME

# Participants
thenvoi-cli participants list ROOM_ID --agent NAME
thenvoi-cli participants add ROOM_ID PEER_ID --agent NAME
thenvoi-cli participants remove ROOM_ID PEER_ID --agent NAME

# Other
thenvoi-cli peers --agent NAME       # Discover peer agents
thenvoi-cli test NAME                # Test connectivity
thenvoi-cli adapters list            # List framework adapters
thenvoi-cli run NAME --adapter TYPE  # Run agent (needs full SDK)
```

## Environment Variables

```bash
THENVOI_REST_URL=https://app.thenvoi.com/
THENVOI_WS_URL=wss://app.thenvoi.com/api/v1/socket/websocket
THENVOI_API_KEY_USER=thnv_u_...      # User API key

# LLM keys (for adapters)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## Output Formats

All commands support `--format` (`-f`) option:
- `table` (default) - Rich tables for humans
- `json` - Machine-readable, pipe to `jq`
- `plain` - Simple text output

```bash
thenvoi-cli --format json agents list | jq '.[].name'
```

## Development

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Test
pytest

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## Key Files to Modify

- Adding new commands: Create in `src/thenvoi_cli/commands/`, register in `cli.py`
- API changes: Update `commands/agents.py` (User API) or `sdk_client.py` (Agent API)
- Output formatting: See `output.py` for `OutputFormat` enum and helpers
- Config handling: See `config_manager.py` for YAML operations
