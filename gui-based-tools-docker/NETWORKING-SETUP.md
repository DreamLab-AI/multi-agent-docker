# MCP Docker Networking Setup Guide

This guide explains how to set up proper networking between the Blender/QGIS MCP container and the multi-agent-docker (Claude agent) container.

## Overview

The MCP (Model Context Protocol) integration requires proper network communication between:
- **Blender Container**: Runs Blender with MCP plugin on port 9876
- **QGIS Container**: Runs QGIS with MCP plugin on port 9877 (may be in same container as Blender)
- **Multi-Agent Docker**: The Claude agent container that needs to connect to the above services

## Network Architecture

```
docker_ragflow network (172.18.0.0/16)
├── blender_desktop (172.18.0.9)
│   ├── Blender MCP: port 9876
│   └── QGIS MCP: port 9877
└── multi_agent_docker (172.18.0.x)
    ├── mcp-blender-client.js → connects to blender_desktop:9876
    └── qgis_mcp.py → connects to blender_desktop:9877
```

## Quick Start

### 1. Using Docker Compose (Recommended)

```bash
cd /workspace/blender-docker

# Start both containers with proper networking
docker-compose -f docker-compose-multi-agent.yml up -d

# Check container status
docker-compose -f docker-compose-multi-agent.yml ps

# View logs
docker-compose -f docker-compose-multi-agent.yml logs -f
```

### 2. Manual Setup (Existing Containers)

If you already have containers running separately:

```bash
# From the host machine, connect multi-agent container to the network
docker network connect docker_ragflow <multi-agent-container-name>

# Inside the multi-agent container, set up environment
source /workspace/blender-docker/setup-mcp-env.sh

# Test connectivity
/workspace/blender-docker/test-mcp-connectivity.sh
```

## Environment Variables

The following environment variables control MCP connectivity:

| Variable | Default | Description |
|----------|---------|-------------|
| `BLENDER_HOST` | `blender_desktop` | Hostname/IP of Blender container |
| `BLENDER_PORT` | `9876` | Port for Blender MCP service |
| `QGIS_HOST` | `blender_desktop` | Hostname/IP of QGIS container |
| `QGIS_PORT` | `9877` | Port for QGIS MCP service |

## Configuration Files

### 1. Docker Compose (`docker-compose.yml`)
- Defines container configuration
- Sets up shared network
- Configures port mappings
- Includes health checks

### 2. MCP Configuration (`.mcp.json`)
- Defines MCP servers and their startup commands
- Bridge scripts use environment variables for connectivity

### 3. Bridge Scripts
- `scripts/mcp-blender-client.js`: Node.js bridge for Blender MCP
- `mcp-tools/qgis_mcp.py`: Python bridge for QGIS MCP

## Testing Connectivity

### 1. Network Connectivity Test
```bash
# Run the comprehensive test script
/workspace/blender-docker/test-mcp-connectivity.sh
```

### 2. Manual Tests
```bash
# Test Blender MCP port
nc -zv blender_desktop 9876

# Test QGIS MCP port  
nc -zv blender_desktop 9877

# Check if on correct network
docker network inspect docker_ragflow
```

### 3. Health Checks
```bash
# Check MCP service health
/workspace/blender-docker/health-check-mcp.sh

# Check specific service
/workspace/blender-docker/health-check-mcp.sh blender
/workspace/blender-docker/health-check-mcp.sh qgis
```

## Troubleshooting

### Container Not on Network
```bash
# Check current networks
docker inspect <container-name> | grep NetworkMode

# Add to network
docker network connect docker_ragflow <container-name>
```

### Connection Refused
1. Check if services are running:
   ```bash
   docker ps | grep blender_desktop
   ```

2. Verify ports are exposed:
   ```bash
   docker port blender_desktop
   ```

3. Check service logs:
   ```bash
   docker logs blender_desktop
   ```

### Environment Variables Not Set
```bash
# Source the setup script
source /workspace/blender-docker/setup-mcp-env.sh

# Verify variables
env | grep -E "(BLENDER|QGIS)_(HOST|PORT)"
```

### MCP Bridge Script Errors
1. Check script logs in Claude's output
2. Verify Node.js/Python dependencies are installed
3. Test manual connection to MCP ports

## Security Considerations

1. **Internal Network Only**: MCP ports should only be accessible within the Docker network
2. **No Public Exposure**: Don't expose MCP ports to host unless necessary
3. **Use Container Names**: Prefer container hostnames over IP addresses for flexibility

## Advanced Configuration

### Custom Network Setup
```yaml
networks:
  custom_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Multiple MCP Services
Add additional services to the docker-compose file:
```yaml
services:
  additional-mcp:
    image: your-mcp-image
    networks:
      - ragflow_network
    environment:
      - MCP_PORT=9878
```

## Monitoring

### Container Logs
```bash
# Follow all logs
docker-compose -f docker-compose-multi-agent.yml logs -f

# Specific container
docker logs -f blender_desktop
```

### Network Traffic
```bash
# Monitor MCP traffic (inside container)
tcpdump -i any -n port 9876 or port 9877
```

## Maintenance

### Restart Services
```bash
# Restart all services
docker-compose -f docker-compose-multi-agent.yml restart

# Restart specific service
docker-compose -f docker-compose-multi-agent.yml restart blender
```

### Update Configuration
1. Edit configuration files
2. Restart affected services
3. Test connectivity

## Integration with Claude

Once properly configured:
1. Claude will spawn local bridge processes defined in `.mcp.json`
2. Bridge scripts connect to remote MCP services using environment variables
3. MCP tools become available in Claude's tool list

To verify integration:
```bash
# List available MCP servers (in Claude)
claude mcp list
```

Expected output should include:
- blender-mcp (connected)
- qgis-mcp (connected)