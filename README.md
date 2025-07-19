# PowerDev Enhanced - MCP Orchestration for Visualization

This enhanced version of the powerdev system adds sophisticated MCP orchestration capabilities designed to support real-time agent swarm visualization projects.

## 🚀 Key Features

### 1. **MCP Orchestrator Service**
- Dedicated service managing all MCP servers
- WebSocket API (port 9001) for real-time data streaming
- REST API (port 9000) for synchronous operations
- Automatic polling of MCP endpoints every 5 seconds
- Caches agent data, token usage, communications, and system health

### 2. **Health Monitoring**
- Comprehensive health checks for all MCP endpoints
- Individual endpoint testing (agents/list, token-usage, memory/query)
- Visual health status reporting
- Automatic service recovery

### 3. **Centralized Logging**
- Loki + Promtail for log aggregation
- JSON-RPC request/response tracking
- Structured logging with searchable metadata
- Log rotation and retention policies

### 4. **Development Tools**
- WebSocket test client with interactive mode
- MCP API testing utilities
- Network debugging tools
- Performance profiling capabilities

### 5. **Optional Services**
- Grafana dashboards for MCP metrics
- Redis caching for improved performance
- Monitoring stack with Prometheus integration

## 📦 Quick Start

### Basic Usage (Main container only)
```bash
# Start the main powerdev container
docker-compose -f docker-compose.enhanced.yml up -d

# Check status
./mcp-scripts/mcp-manager.sh status

# Run health checks
./mcp-scripts/mcp-manager.sh health
```

### With Monitoring
```bash
# Start with Grafana monitoring
docker-compose -f docker-compose.enhanced.yml --profile monitoring up -d

# Access Grafana at http://localhost:3002
# Default credentials: admin/admin
```

### With Development Tools
```bash
# Start with development utilities
docker-compose -f docker-compose.enhanced.yml --profile tools up -d

# Access tools container
./mcp-scripts/mcp-manager.sh shell tools

# Test WebSocket connection
python3 /app/ws-test-client.py --interactive
```

## 🔌 WebSocket API for Visualization

The MCP Orchestrator exposes a WebSocket API specifically designed for real-time visualization:

### Connection
```javascript
const ws = new WebSocket('ws://localhost:9001');
```

### Data Structure
```javascript
{
  "agents": [
    {
      "id": "agent-123",
      "type": "coder",
      "status": "busy",
      "health": 95,
      "cpuUsage": 45.2,
      "memoryUsage": 62.1,
      "createdAt": "2024-01-15T09:00:00Z"
    }
  ],
  "communications": [
    {
      "timestamp": "2024-01-15T10:29:55Z",
      "sender": "agent-123",
      "receivers": ["agent-456", "agent-789"],
      "metadata": {
        "size": 2048,
        "type": "task-assignment"
      }
    }
  ],
  "tokenUsage": {
    "total": 150000,
    "byAgent": {
      "coder": 50000,
      "tester": 30000
    }
  }
}
```

## 🛠️ Management Commands

The `mcp-manager.sh` script provides convenient commands:

```bash
# Service management
./mcp-scripts/mcp-manager.sh start [profile]     # Start services
./mcp-scripts/mcp-manager.sh stop               # Stop all services
./mcp-scripts/mcp-manager.sh restart            # Restart services
./mcp-scripts/mcp-manager.sh status             # Show status

# Debugging
./mcp-scripts/mcp-manager.sh logs [service]     # View logs
./mcp-scripts/mcp-manager.sh health             # Run health checks
./mcp-scripts/mcp-manager.sh test-ws            # Test WebSocket
./mcp-scripts/mcp-manager.sh test-api           # Test REST API

# Development
./mcp-scripts/mcp-manager.sh shell [service]    # Open shell
./mcp-scripts/mcp-manager.sh update             # Update images
```

## 🏗️ Architecture

```
┌─────────────────────┐     ┌──────────────────┐
│  Visualization App  │────▶│ MCP Orchestrator │
└─────────────────────┘     └──────────────────┘
                                     │
                  ┌──────────────────┼──────────────────┐
                  │                  │                  │
           ┌──────▼────┐      ┌─────▼─────┐     ┌─────▼──────┐
           │Claude Flow│      │  Blender  │     │   Revit    │
           │   MCP     │      │    MCP    │     │    MCP     │
           └───────────┘      └───────────┘     └────────────┘
```

## 📊 Monitoring

Access Grafana dashboards at `http://localhost:3002`:

1. **MCP Request Rate** - Requests per second by tool
2. **Error Rate** - MCP errors over time
3. **Tool Usage** - Distribution of MCP tool calls
4. **Request Duration** - Average response times
5. **System Logs** - Searchable log viewer

## 🔧 Configuration

### Environment Variables
```bash
# MCP Orchestrator
MCP_ORCHESTRATOR_PORT=9000
WEBSOCKET_PORT=9001
POLL_INTERVAL=5000
LOG_LEVEL=debug

# Remote MCP Host (if using external servers)
REMOTE_MCP_HOST=192.168.1.100

# Grafana
GRAFANA_PASSWORD=your-secure-password
```

### Network Configuration
- All services use the `powerdev-net` bridge network
- Static IPs assigned for consistent service discovery
- Cross-container communication enabled

## 🐞 Troubleshooting

### MCP Server Not Responding
```bash
# Check if services are running
docker ps | grep powerdev

# Check MCP server logs
./mcp-scripts/mcp-manager.sh logs orchestrator

# Test individual endpoints
curl http://localhost:9000/health | jq .
```

### WebSocket Connection Issues
```bash
# Test WebSocket connectivity
wscat -c ws://localhost:9001

# Check orchestrator logs for errors
docker logs powerdev-mcp-orchestrator
```

### Performance Issues
```bash
# Enable Redis caching
docker-compose -f docker-compose.enhanced.yml --profile cache up -d

# Monitor resource usage
docker stats powerdev-main powerdev-mcp-orchestrator
```

## 📚 API Documentation

Complete API documentation is available in `MCP_VISUALIZATION_API.md`, including:
- WebSocket message formats
- REST API endpoints
- Data structures
- Integration examples
- Rate limits and error handling

## 🔐 Security Considerations

1. **Default passwords** - Change Grafana passwords in production
2. **Network isolation** - Use custom networks for service isolation
3. **Rate limiting** - REST API limited to 100 requests per 15 minutes
4. **Authentication** - Add authentication for production deployments

## 🚧 Future Enhancements

- [ ] Kubernetes deployment manifests
- [ ] Horizontal scaling support
- [ ] Advanced caching strategies
- [ ] Machine learning integration
- [ ] Custom MCP tool development

## 📝 License

This enhanced powerdev system maintains the same license as the original project.