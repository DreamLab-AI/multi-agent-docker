# Blender-Docker MCP Networking

This directory contains configurations and scripts to enable MCP (Model Context Protocol) communication between the Blender/QGIS container and multi-agent-docker containers.

## Quick Start

```bash
# 1. Start containers with proper networking
docker-compose -f docker-compose-multi-agent.yml up -d

# 2. In the agent container, setup environment
source setup-mcp-env.sh

# 3. Test connectivity
./test-mcp-connectivity.sh
```

## Files Overview

- **docker-compose.yml** - Basic Blender container configuration
- **docker-compose-multi-agent.yml** - Full setup with multi-agent-docker
- **setup-mcp-env.sh** - Environment variable configuration script
- **test-mcp-connectivity.sh** - Comprehensive connectivity test
- **health-check-mcp.sh** - Health check script for MCP services
- **configure-hosts.sh** - Hostname resolution setup
- **NETWORKING-SETUP.md** - Detailed networking documentation
- **TROUBLESHOOTING.md** - Common issues and solutions

## Key Changes from Original Setup

1. **Exposed MCP Ports**: Added ports 9876 (Blender) and 9877 (QGIS) to docker-compose
2. **Hostname Configuration**: Added explicit hostname for DNS resolution
3. **Environment Variables**: Bridge scripts now use BLENDER_HOST/QGIS_HOST instead of hardcoded localhost
4. **Health Checks**: Added Docker health checks for MCP services
5. **Network Configuration**: Ensures all containers use the same Docker network (docker_ragflow)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   docker_ragflow network                 │
├─────────────────────────┬───────────────────────────────┤
│   blender_desktop       │    multi_agent_docker         │
│   ┌─────────────────┐   │   ┌──────────────────────┐   │
│   │ Blender + MCP   │   │   │  Claude Agent        │   │
│   │ Port: 9876      │◄──┼───┤  mcp-blender-client  │   │
│   └─────────────────┘   │   └──────────────────────┘   │
│   ┌─────────────────┐   │   ┌──────────────────────┐   │
│   │ QGIS + MCP      │   │   │  Claude Agent        │   │
│   │ Port: 9877      │◄──┼───┤  qgis_mcp.py         │   │
│   └─────────────────┘   │   └──────────────────────┘   │
└─────────────────────────┴───────────────────────────────┘
```

## Testing

After setup, the MCP tools should appear in Claude's tool list:
- `blender-mcp` - For Blender operations
- `qgis-mcp` - For QGIS operations

Test with:
```bash
# In Claude
claude mcp list
```

## Support

- See [NETWORKING-SETUP.md](./NETWORKING-SETUP.md) for detailed setup
- See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues
- Check `/workspace/mcp-integration-report.md` for architectural details