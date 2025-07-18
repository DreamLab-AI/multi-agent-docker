# MCP Server Integration Plan for Claude Code

## Overview
This document provides a step-by-step plan for integrating multiple MCP servers into Claude Code, with special attention to the Blender MCP server that requires network connectivity from within a Docker container.

## Current State Analysis

### Existing MCP Servers
1. **ruv-swarm**: Multi-agent orchestration (stdio mode)
   - Command: `npx ruv-swarm mcp start`
   - Already configured in Claude Code

2. **claude-flow**: Advanced coordination features (stdio mode)
   - Command: `npx claude-flow@alpha mcp start`
   - Already configured in Claude Code

### MCP Configuration Structure
- MCP servers are configured in Claude Code settings
- Two main connection types:
  - **stdio**: Direct process communication (most common)
  - **Network**: TCP/IP connection (needed for Blender)

## Integration Steps

### Step 1: Blender MCP Server Configuration

#### A. Network Connection Setup
The Blender MCP server runs inside a Docker container on port 9876. To connect from the host:

1. **From Host Machine (Claude Code on host):**
   ```bash
   # Method 1: Using uvx (recommended)
   claude mcp add blender uvx blender-mcp
   
   # Method 2: Using direct connection
   claude mcp add-json blender '{
     "transport": "tcp",
     "host": "localhost",
     "port": 9876
   }'
   ```

2. **From Inside Container (if Claude Code runs in container):**
   ```bash
   # Direct localhost connection
   claude mcp add-json blender '{
     "transport": "tcp", 
     "host": "localhost",
     "port": 9876
   }'
   ```

#### B. Docker Network Considerations
- Container exposes port 9876 to host
- Uses `host.docker.internal` for container-to-host communication
- Xvfb display :99 for headless rendering

### Step 2: GitHub MCP Server Integration

```bash
# Add GitHub MCP server
claude mcp add github npx @modelcontextprotocol/server-github
```

Configuration notes:
- Requires GITHUB_TOKEN environment variable
- Provides repository analysis and PR management
- Works in stdio mode

### Step 3: Filesystem MCP Server Integration

```bash
# Add filesystem MCP server
claude mcp add filesystem npx @modelcontextprotocol/server-filesystem --allowed-directories /workspace
```

Configuration notes:
- Specify allowed directories for security
- Useful for advanced file operations
- Works in stdio mode

### Step 4: PostgreSQL MCP Server Integration

```bash
# Add PostgreSQL MCP server
claude mcp add postgres npx @modelcontextprotocol/server-postgres
```

Configuration notes:
- Requires DATABASE_URL environment variable
- Format: `postgresql://user:password@host:port/database`
- Works in stdio mode

### Step 5: Puppeteer MCP Server Integration

```bash
# Add Puppeteer MCP server
claude mcp add puppeteer npx @modelcontextprotocol/server-puppeteer
```

Configuration notes:
- For web automation and testing
- Requires Chrome/Chromium installed
- Works in stdio mode

### Step 6: Fetch MCP Server Integration

```bash
# Add Fetch MCP server
claude mcp add fetch npx @modelcontextprotocol/server-fetch
```

Configuration notes:
- For HTTP requests and web scraping
- No special configuration needed
- Works in stdio mode

## Configuration File Structure

After adding all servers, the `.claude/settings.json` should include:

```json
{
  "mcpServers": {
    "ruv-swarm": {
      "command": "npx",
      "args": ["ruv-swarm", "mcp", "start"],
      "env": {
        "RUV_SWARM_HOOKS_ENABLED": "false",
        "RUV_SWARM_TELEMETRY_ENABLED": "true"
      }
    },
    "claude-flow": {
      "command": "npx",
      "args": ["claude-flow@alpha", "mcp", "start"]
    },
    "blender": {
      "transport": "tcp",
      "host": "localhost",
      "port": 9876
    },
    "github": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem", "--allowed-directories", "/workspace"]
    },
    "postgres": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}"
      }
    },
    "puppeteer": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-puppeteer"]
    },
    "fetch": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-fetch"]
    }
  }
}
```

## Verification Steps

### 1. List all configured servers:
```bash
claude mcp list
```

### 2. Test each server:
```bash
# In Claude Code, use the MCP tools:
# For Blender:
mcp__blender__get_scene_info

# For GitHub:
mcp__github__search_repositories

# For filesystem:
mcp__filesystem__read_file

# etc.
```

### 3. Check server logs:
```bash
# For stdio servers
claude mcp logs <server-name>

# For Blender (TCP server)
docker logs <container-name> | grep blender-mcp
```

## Troubleshooting

### Common Issues:

1. **Blender Connection Failed**
   - Check if container is running: `docker ps`
   - Verify port is exposed: `docker port <container> 9876`
   - Test connection: `telnet localhost 9876`

2. **Stdio Server Not Starting**
   - Check npm package exists: `npm view <package-name>`
   - Verify command syntax in settings.json
   - Check environment variables are set

3. **Permission Denied**
   - For filesystem server: verify allowed directories
   - For GitHub: check token permissions
   - For postgres: verify database credentials

### Debug Commands:

```bash
# Get detailed server info
claude mcp get <server-name>

# Remove and re-add a server
claude mcp remove <server-name>
claude mcp add <server-name> <command>

# Reset all project choices
claude mcp reset-project-choices
```

## Best Practices

1. **Security**
   - Limit filesystem access to specific directories
   - Use environment variables for sensitive data
   - Review server permissions before adding

2. **Performance**
   - Stdio servers are more efficient than network servers
   - Batch operations when possible
   - Monitor server resource usage

3. **Maintenance**
   - Regularly update MCP packages
   - Document custom server configurations
   - Test servers after system updates

## Next Steps

1. Implement the integration steps above
2. Create test scripts for each server
3. Document server-specific capabilities
4. Set up monitoring for server health
5. Create example workflows combining multiple servers

## References

- [MCP Documentation](https://modelcontextprotocol.io)
- [Claude Code MCP Guide](https://claude.ai/docs/mcp)
- [Blender MCP Repository](https://github.com/blender-mcp/blender-mcp)
- Docker Networking: host.docker.internal for container-to-host communication