# Getting Started with thenvoi-cli

This guide will help you get started with thenvoi-cli in under 5 minutes.

## Prerequisites

- Linux (x86_64 or ARM64)
- A Thenvoi platform account
- An agent created on the Thenvoi platform

## Installation

### Option 1: Binary (Recommended)

Download and install the standalone binary:

```bash
curl -fsSL https://raw.githubusercontent.com/bacedia/thenvoi-cli/main/install.sh | bash
```

This installs `thenvoi-cli` to `/usr/local/bin` (or `~/.local/bin` if you don't have write access).

### Option 2: pip/pipx

```bash
# Using pipx (isolated environment)
pipx install thenvoi-cli

# Or using pip
pip install thenvoi-cli
```

For adapter-specific dependencies:

```bash
pip install thenvoi-cli[langgraph]   # For LangGraph
pip install thenvoi-cli[anthropic]   # For Anthropic
pip install thenvoi-cli[all]         # All adapters
```

## Configuration

### Step 1: Get Your Agent Credentials

1. Log in to the Thenvoi platform
2. Navigate to your agent's settings
3. Copy the **Agent ID** (UUID format)
4. Generate and copy the **API Key** (shown only once!)

### Step 2: Configure the CLI

```bash
thenvoi-cli config set my-agent \
  --agent-id 12345678-1234-1234-1234-123456789012 \
  --api-key sk-your-api-key-here
```

### Step 3: Set Environment Variables

Add these to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
# Thenvoi platform URLs
export THENVOI_REST_URL=https://app.thenvoi.com/
export THENVOI_WS_URL=wss://app.thenvoi.com/api/v1/socket/websocket

# LLM API key (choose based on your adapter)
export OPENAI_API_KEY=sk-your-openai-key
# OR
export ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
```

### Step 4: Verify Configuration

```bash
# Test your setup
thenvoi-cli test my-agent
```

You should see all checks pass:

```
Testing agent 'my-agent'...

Configuration:
  PASS Config file: Found
  PASS Agent config: Found
  PASS Agent ID format: Valid UUID
  PASS Environment vars: All required variables set

Connectivity:
  PASS REST API: Reachable (245ms)
  PASS Authentication: Credentials accepted

All 6 checks passed
```

## Running Your First Agent

```bash
# Run with the default adapter (LangGraph)
thenvoi-cli run my-agent

# Or specify an adapter
thenvoi-cli run my-agent --adapter anthropic --model claude-sonnet-4-5-20250929
```

The agent will connect to the platform and start responding to messages in its assigned rooms.

Press `Ctrl+C` to stop the agent gracefully.

## Background Mode

For long-running agents:

```bash
# Start in background
thenvoi-cli run my-agent --background

# Check status
thenvoi-cli status

# Stop when done
thenvoi-cli stop my-agent
```

## Next Steps

- [Command Reference](commands/README.md) - Full command documentation
- [Adapter Guides](adapters/README.md) - Framework-specific configuration
- [Examples](examples/README.md) - Common use cases and scripts
