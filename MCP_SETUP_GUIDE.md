# MCP Server Setup Guide for Multi-Agent Docker

This guide documents the MCP (Model Context Protocol) server setup and configuration for the multi-agent Docker environment, including Claude Flow, Ruv Swarm, and Blender MCP integration.

## Overview

The multi-agent Docker environment now includes full MCP support with:
- **Claude Flow**: Swarm orchestration and coordination
- **Ruv Swarm**: Advanced agent management
- **Blender MCP**: 3D modeling and rendering via remote connection
- **Internal MCP Tools**: A suite of tools running inside the container, including:
  - `imagemagick-mcp`: Image processing via ImageMagick.
  - `pbr-generator-mcp`: PBR texture generation.
  - `ngspice-mcp`: Electronic circuit simulation with NGSpice.

## Key Changes Made

### 1. MCP Configuration Files

#### `/workspace/.mcp.json`
Updated to include all three MCP servers with proper configuration:
```json
{
  "mcpServers": {
    "claude-flow": {
      "command": "npx",
      "args": ["claude-flow@alpha", "mcp", "start"],
      "type": "stdio"
    },
    "ruv-swarm": {
      "command": "npx",
      "args": ["ruv-swarm@latest", "mcp", "start"],
      "type": "stdio"
    },
    "blender-tcp": {
      "command": "node",
      "args": ["/workspace/mcp-blender-client.js"],
      "type": "stdio",
      "env": {
        "BLENDER_HOST": "192.168.0.216",
        "BLENDER_PORT": "9876"
      }
    }
  }
}
```

### 2. Blender MCP Bridge

#### `/workspace/mcp-blender-client.js`
Created a Node.js bridge script that:
- Connects to remote Blender MCP server via TCP
- Translates between stdio (Claude) and TCP (Blender) protocols
- Handles reconnection logic and error recovery
- Supports configurable host/port via environment variables

### 3. Docker Networking

#### `docker-compose.yml` Updates
- Added `blender-host` to extra_hosts for direct IP mapping
- Exposed additional ports for development servers
- Maintained proper network isolation with bridge networking

### 4. Initialization Scripts

#### `/workspace/init-mcp-servers.sh`
Comprehensive initialization script that:
- Installs/updates Claude Flow and Ruv Swarm
- Configures MCP settings
- Tests MCP server connectivity
- Creates helper scripts

#### Helper Scripts Created:
- `/workspace/mcp-status.sh`: Check status of all MCP servers
- `/workspace/test-blender-mcp.sh`: Test Blender MCP connection

### 5. PowerDev CLI Enhancements

#### `powerdev.sh` Updates
Added new `mcp` command with subcommands:
- `./powerdev.sh mcp status`: Check MCP server status
- `./powerdev.sh mcp init`: Initialize MCP servers
- `./powerdev.sh mcp test-blender`: Test Blender connection
- `./powerdev.sh mcp logs`: View MCP logs

## Network Architecture

### Host Networking Workaround
For accessing Blender MCP on a remote host (192.168.0.216):

1. **Direct IP Mapping**: Added to docker-compose.yml:
   ```yaml
   extra_hosts:
     - "blender-host:192.168.0.216"
   ```

2. **Bridge Script**: The `mcp-blender-client.js` acts as a protocol bridge

3. **Environment Variables**: Configure in `.env` or at runtime:
   ```bash
   BLENDER_HOST=192.168.0.216
   BLENDER_PORT=9876
   ```

## Usage Instructions

### Quick Start

1. **Start the environment**:
   ```bash
   ./powerdev.sh start
   ```
   The MCP servers will be automatically initialized on first start.

2. **Check MCP status**:
   ```bash
   ./powerdev.sh mcp status
   ```

3. **Test Blender connection**:
   ```bash
   ./powerdev.sh mcp test-blender
   ```

### Manual Configuration

If you need to manually configure or troubleshoot:

1. **Enter the container**:
   ```bash
   ./powerdev.sh shell
   ```

2. **Run initialization**:
   ```bash
   cd /workspace
   ./init-mcp-servers.sh
   ```

3. **Check status**:
   ```bash
   ./mcp-status.sh
   ```

### Using MCP Tools in Claude

Once configured, MCP tools are available with the `mcp__` prefix:

- **Claude Flow**: `mcp__claude-flow__*`
- **Ruv Swarm**: `mcp__ruv-swarm__*`
- **Blender**: `mcp__blender__*` (when connected)
- **ImageMagick**: `mcp__imagemagick__*`
- **PBR Generator**: `mcp__pbr_generator__*`
- **NGSpice**: `mcp__ngspice__*`

Example:
```javascript
// Initialize a swarm
mcp__claude-flow__swarm_init({ topology: "mesh", maxAgents: 5 })

// Create a Blender scene
mcp__blender__create_scene({ name: "MyScene" })
```

## Troubleshooting

### Blender MCP Connection Issues

1. **Check connectivity**:
   ```bash
   nc -zv 192.168.0.216 9876
   ```

2. **Verify Blender is running** with MCP addon enabled

3. **Check firewall** on the Blender host allows port 9876

4. **Test with different IP**:
   ```bash
   BLENDER_HOST=<your-ip> ./test-blender-mcp.sh
   ```

### MCP Server Issues

1. **Check logs**:
   ```bash
   ./powerdev.sh mcp logs
   ```

2. **Reinstall servers**:
   ```bash
   npm install -g claude-flow@alpha --force
   npm install -g ruv-swarm@latest --force
   ```

3. **Clear cache**:
   ```bash
   rm -rf ~/.npm/_cacache
   ```

## Security Considerations

- The Blender MCP bridge runs with limited permissions
- TCP connections are not encrypted (use VPN for remote connections)
- Environment variables can override default configurations
- All MCP servers run as non-root user (uid 1000)

## Future Enhancements

1. **SSL/TLS Support**: Add encrypted connections for remote MCP servers
2. **Service Discovery**: Automatic discovery of MCP servers on the network
3. **Load Balancing**: Multiple Blender instances for rendering farms
4. **Monitoring**: Grafana dashboards for MCP performance metrics

## References

- [Claude Flow Documentation](https://github.com/ruvnet/claude-flow)
- [Ruv Swarm Documentation](https://github.com/ruvnet/ruv-swarm)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Blender MCP Addon](https://github.com/mcp-blender/blender-addon)