# thenvoi-cli

Command-line interface for the [Thenvoi](https://thenvoi.com) AI agent platform.

[![CI](https://github.com/bacedia/thenvoi-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/bacedia/thenvoi-cli/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/thenvoi-cli.svg)](https://badge.fury.io/py/thenvoi-cli)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Quick Install

**Binary (recommended):**
```bash
curl -fsSL https://raw.githubusercontent.com/bacedia/thenvoi-cli/main/install.sh | bash
```

**pip:**
```bash
pip install thenvoi-cli
```

**pipx:**
```bash
pipx install thenvoi-cli
```

## Quick Start

```bash
# 1. Configure your agent (get credentials from Thenvoi platform)
thenvoi-cli config set my-agent \
  --agent-id 12345678-1234-1234-1234-123456789012 \
  --api-key sk-your-api-key

# 2. Set platform URLs
export THENVOI_REST_URL=https://app.thenvoi.com/
export THENVOI_WS_URL=wss://app.thenvoi.com/api/v1/socket/websocket

# 3. Set LLM API key (for your chosen adapter)
export OPENAI_API_KEY=sk-your-openai-key
# or
export ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# 4. Run your agent
thenvoi-cli run my-agent --adapter langgraph
```

## Commands

| Command | Description |
|---------|-------------|
| `thenvoi-cli run <agent>` | Run an agent connected to the platform |
| `thenvoi-cli status` | Show status of running agents |
| `thenvoi-cli stop <agent>` | Stop a running agent |
| `thenvoi-cli config set` | Save agent credentials |
| `thenvoi-cli config list` | List configured agents |
| `thenvoi-cli config show` | Show agent configuration |
| `thenvoi-cli rooms list` | List chat rooms |
| `thenvoi-cli rooms send` | Send a message to a room |
| `thenvoi-cli participants list` | List room participants |
| `thenvoi-cli peers` | Discover available peer agents |
| `thenvoi-cli adapters list` | List available adapters |
| `thenvoi-cli test <agent>` | Test configuration and connectivity |

## Adapters

thenvoi-cli supports multiple AI frameworks:

| Adapter | Framework | Default Model | Install |
|---------|-----------|---------------|---------|
| `langgraph` | LangGraph | gpt-4o | `pip install thenvoi-cli[langgraph]` |
| `anthropic` | Anthropic SDK | claude-sonnet-4-5-20250929 | `pip install thenvoi-cli[anthropic]` |
| `claude-sdk` | Claude Agent SDK | claude-sonnet-4-5-20250929 | `pip install thenvoi-cli[claude-sdk]` |
| `pydantic-ai` | Pydantic AI | openai:gpt-4o | `pip install thenvoi-cli[pydantic-ai]` |
| `crewai` | CrewAI | gpt-4o | `pip install thenvoi-cli[crewai]` |
| `parlant` | Parlant | gpt-4o | `pip install thenvoi-cli[parlant]` |
| `a2a` | A2A Protocol | - | `pip install thenvoi-cli[a2a]` |

```bash
# Check adapter availability
thenvoi-cli adapters list

# Get adapter details
thenvoi-cli adapters info langgraph
```

## Output Formats

All commands support multiple output formats for scripting and automation:

```bash
# JSON output (great for jq, Claude, scripts)
thenvoi-cli rooms list --agent my-agent --format json

# Table output (default, human-readable)
thenvoi-cli rooms list --agent my-agent --format table

# Plain text
thenvoi-cli rooms list --agent my-agent --format plain
```

## Configuration

### Agent Configuration

Stored in `agent_config.yaml`:

```yaml
my-agent:
  agent_id: "12345678-1234-1234-1234-123456789012"
  api_key: "sk-your-api-key"

another-agent:
  agent_id: "87654321-4321-4321-4321-210987654321"
  api_key: "sk-another-key"
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `THENVOI_REST_URL` | REST API URL (required) |
| `THENVOI_WS_URL` | WebSocket URL (required) |
| `THENVOI_AGENT_ID` | Override agent ID |
| `THENVOI_API_KEY` | Override API key |
| `THENVOI_CONFIG_PATH` | Custom config file path |
| `OPENAI_API_KEY` | For LangGraph, CrewAI, Parlant adapters |
| `ANTHROPIC_API_KEY` | For Anthropic, Claude SDK adapters |

## Examples

### Run an Agent in the Background

```bash
# Start in background
thenvoi-cli run my-agent --adapter langgraph --background

# Check status
thenvoi-cli status

# Stop when done
thenvoi-cli stop my-agent
```

### Send Messages from Scripts

```bash
# Send a message
thenvoi-cli rooms send room-123 "Task completed" \
  --agent my-agent \
  --mentions User

# Send from stdin
echo "Multi-line
message here" | thenvoi-cli rooms send room-123 - --agent my-agent
```

### Use with Claude/AI Automation

```bash
# Get rooms as JSON
rooms=$(thenvoi-cli rooms list --agent my-agent --format json)

# Parse with jq
room_id=$(echo "$rooms" | jq -r '.[0].id')

# Send message
thenvoi-cli rooms send "$room_id" "Automated message" --agent my-agent
```

### Test Connectivity

```bash
# Full connectivity test
thenvoi-cli test my-agent

# Config validation only
thenvoi-cli test my-agent --config-only
```

## Troubleshooting

### "Agent not found"
```bash
# List available agents
thenvoi-cli config list

# Add missing agent
thenvoi-cli config set my-agent --agent-id <uuid> --api-key <key>
```

### "THENVOI_REST_URL not set"
```bash
export THENVOI_REST_URL=https://app.thenvoi.com/
export THENVOI_WS_URL=wss://app.thenvoi.com/api/v1/socket/websocket
```

### "Missing dependencies"
```bash
# Install adapter dependencies
pip install thenvoi-cli[langgraph]

# Or all adapters
pip install thenvoi-cli[all]
```

### Debug Mode
```bash
# Full tracebacks and debug output
thenvoi-cli run my-agent --debug
```

## Development

```bash
# Clone repo
git clone https://github.com/bacedia/thenvoi-cli
cd thenvoi-cli

# Install in dev mode
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## License

MIT License - see [LICENSE](LICENSE) for details.
