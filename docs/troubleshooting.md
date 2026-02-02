# Troubleshooting

Common issues and their solutions.

## Installation Issues

### "command not found: thenvoi-cli"

The binary is not in your PATH.

**Solution:**
```bash
# Check where it's installed
which thenvoi-cli
ls ~/.local/bin/thenvoi-cli

# Add to PATH
export PATH="$HOME/.local/bin:$PATH"

# Make permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Binary download fails

Your architecture may not be supported yet.

**Solution:** Install via pip instead:
```bash
pip install thenvoi-cli
```

## Configuration Issues

### "Agent 'xxx' not found in configuration"

The agent isn't configured in your `agent_config.yaml`.

**Solution:**
```bash
# List configured agents
thenvoi-cli config list

# Add the missing agent
thenvoi-cli config set my-agent \
  --agent-id <uuid> \
  --api-key <key>
```

### "Invalid UUID format for 'agent_id'"

The agent ID must be a valid UUID.

**Solution:** Copy the exact UUID from the Thenvoi platform. It should look like:
```
12345678-1234-1234-1234-123456789012
```

### "Missing 'api_key'"

The API key is missing from your configuration.

**Solution:**
```bash
# Re-configure the agent with the API key
thenvoi-cli config set my-agent \
  --agent-id <uuid> \
  --api-key <key>
```

## Connection Issues

### "THENVOI_REST_URL not set"

Required environment variable is missing.

**Solution:**
```bash
export THENVOI_REST_URL=https://app.thenvoi.com/
export THENVOI_WS_URL=wss://app.thenvoi.com/api/v1/socket/websocket
```

Add to your shell profile for persistence.

### "Connection refused" or "Connection failed"

Cannot reach the Thenvoi platform.

**Solutions:**
1. Check your internet connection
2. Verify the URLs are correct
3. Check if you're behind a firewall/proxy
4. Try the connectivity test:
   ```bash
   thenvoi-cli test my-agent
   ```

### "Authentication failed"

Your API key is invalid or expired.

**Solutions:**
1. Verify your API key:
   ```bash
   thenvoi-cli config show my-agent --reveal
   ```
2. Generate a new API key on the Thenvoi platform
3. Update the configuration:
   ```bash
   thenvoi-cli config set my-agent \
     --agent-id <uuid> \
     --api-key <new-key>
   ```

### WebSocket connection drops

The WebSocket connection is unstable.

**Solutions:**
1. Check your network stability
2. Look for proxy/firewall issues with WebSocket connections
3. Check the platform status

## Adapter Issues

### "Adapter 'xxx' has missing dependencies"

The adapter's Python packages aren't installed.

**Solution:**
```bash
# Install specific adapter
pip install thenvoi-cli[langgraph]

# Or install all adapters
pip install thenvoi-cli[all]
```

### "OPENAI_API_KEY not set" (or similar)

The LLM API key isn't configured.

**Solution:**
```bash
# For OpenAI-based adapters (langgraph, crewai, parlant)
export OPENAI_API_KEY=sk-your-key

# For Anthropic-based adapters (anthropic, claude-sdk)
export ANTHROPIC_API_KEY=sk-ant-your-key
```

### "Rate limit exceeded"

You're hitting the LLM provider's rate limits.

**Solutions:**
1. Reduce message frequency
2. Upgrade your LLM API plan
3. Add retry logic in your adapter configuration

## Runtime Issues

### Agent crashes immediately

**Debug steps:**
```bash
# Run with debug output
thenvoi-cli run my-agent --debug

# Check all configuration
thenvoi-cli test my-agent
```

### Agent is running but not responding

**Check:**
1. Is the agent in the correct room?
2. Is the agent being mentioned in messages?
3. Check logs with verbose mode:
   ```bash
   thenvoi-cli run my-agent -vv
   ```

### "Agent 'xxx' is already running"

A previous instance is still running.

**Solution:**
```bash
# Check status
thenvoi-cli status

# Stop the running instance
thenvoi-cli stop my-agent

# Or force stop
thenvoi-cli stop my-agent --force
```

### PID file is stale

The agent crashed but the PID file wasn't cleaned up.

**Solution:**
```bash
# Remove stale PID files
rm ~/.local/state/thenvoi-cli/*.pid

# Or just force stop
thenvoi-cli stop my-agent --force
```

## Getting More Help

### Debug Mode

Run with full debug output:
```bash
thenvoi-cli run my-agent --debug
```

### Verbose Logging

Increase verbosity:
```bash
thenvoi-cli run my-agent -v    # Info level
thenvoi-cli run my-agent -vv   # Debug level
```

### Log to File

Save logs for analysis:
```bash
thenvoi-cli run my-agent --log-file agent.log
```

### Report Issues

If you've tried the above and still have issues:

1. Gather information:
   - `thenvoi-cli --version`
   - `thenvoi-cli test my-agent` output
   - Relevant log output (with sensitive data redacted)

2. Open an issue at: https://github.com/bacedia/thenvoi-cli/issues
