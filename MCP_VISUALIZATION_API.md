# MCP Services Documentation

This document describes the MCP (Model Context Protocol) services available in the PowerDev environment.

## Overview

The PowerDev environment includes a suite of internal MCP tools that are managed by `supervisord`. These tools provide access to a wide range of capabilities, from content creation to electronic design automation. A simple WebSocket relay on port 3002 is provided for agents to connect to these services.

## Available MCP Tools

The following MCP tools are started automatically by `supervisord`:

- **`imagemagick-mcp`**: Exposes [ImageMagick's](https://imagemagick.org/) powerful image processing capabilities.
  - **Tool Prefix**: `mcp__imagemagick__*`
- **`pbr-generator-mcp`**: Provides access to the `tessellating-pbr-generator` for creating high-quality, seamless PBR materials.
  - **Tool Prefix**: `mcp__pbr_generator__*`
- **`ngspice-mcp`**: Allows for SPICE simulation of electronic circuits using [NGSpice](http://ngspice.sourceforge.net/).
  - **Tool Prefix**: `mcp__ngspice__*`

## Connection

Agents connect to the MCP services through the WebSocket relay on port 3002.

```javascript
const ws = new WebSocket('ws://localhost:3002');
```

### Message Types

#### 1. Welcome Message (Server → Client)
Sent immediately upon connection with initial data.

```json
{
  "type": "welcome",
  "clientId": "uuid-v4",
  "data": {
    "agents": [...],
    "tokenUsage": {...},
    "communications": [...],
    "systemHealth": {...},
    "lastUpdate": "2024-01-15T10:30:00Z"
  }
}
```

#### 2. MCP Update (Server → Client)
Broadcast every 5 seconds with latest data.

```json
{
  "type": "mcp-update",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "agents": [
      {
        "id": "agent-123",
        "type": "coder",
        "status": "busy",
        "health": 95,
        "cpuUsage": 45.2,
        "memoryUsage": 62.1,
        "createdAt": "2024-01-15T09:00:00Z",
        "age": 5400000
      }
    ],
    "tokenUsage": {
      "total": 150000,
      "byAgent": {
        "coder": 50000,
        "tester": 30000,
        "coordinator": 70000
      }
    },
    "communications": [
      {
        "id": "comm-456",
        "type": "communication",
        "timestamp": "2024-01-15T10:29:55Z",
        "sender": "agent-123",
        "receivers": ["agent-456", "agent-789"],
        "metadata": {
          "size": 2048,
          "type": "task-assignment"
        }
      }
    ],
    "systemHealth": {
      "overall": "healthy",
      "services": {
        "claude-flow": "up",
        "mcp-servers": "up"
      }
    }
  }
}
```

#### 3. Subscribe (Client → Server)
Subscribe to specific data streams.

```json
{
  "type": "subscribe",
  "topics": ["agents", "communications"]
}
```

#### 4. MCP Request (Client → Server)
Direct MCP tool invocation.

```json
{
  "type": "mcp-request",
  "requestId": "req-789",
  "tool": "agents/list",
  "params": {}
}
```

#### 5. MCP Response (Server → Client)

```json
{
  "type": "mcp-response",
  "requestId": "req-789",
  "tool": "agents/list",
  "result": {...}
}
```

#### 6. MCP Error (Server → Client)

```json
{
  "type": "mcp-error",
  "requestId": "req-789",
  "tool": "agents/list",
  "error": "Connection timeout"
}
```

#### 7. Ping/Pong (Keepalive)

```json
// Client → Server
{ "type": "ping" }

// Server → Client
{ "type": "pong", "timestamp": "2024-01-15T10:30:00Z" }
```

## WebSocket API (ws://localhost:3002)

### Health & Status

The health of individual MCP services can be monitored through `supervisorctl`:

```bash
# From inside the container
supervisorctl status

# Or using the powerdev.sh script from the host
./powerdev.sh mcp status
```

### GET /api/mcp/data
Get current cached MCP data.

**Response:**
```json
{
  "agents": [...],
  "tokenUsage": {...},
  "communications": [...],
  "systemHealth": {...},
  "lastUpdate": "2024-01-15T10:30:00Z"
}
```

### POST /api/mcp/tool
Execute MCP tool directly.

**Request:**
```json
{
  "tool": "agents/list",
  "params": {}
}
```

**Response:**
```json
{
  "success": true,
  "result": {...}
}
```

### GET /api/mcp/servers
Get MCP server configuration.

**Response:**
```json
{
  "servers": [
    { "name": "blender", "port": 9876 },
    { "name": "revit", "port": 8080 },
    { "name": "unreal", "port": 55557 }
  ],
  "claudeFlow": {
    "host": "powerdev-main",
    "port": 3000
  }
}
```

## Data Structures

### Agent Object
```typescript
interface Agent {
  id: string;
  type: 'coder' | 'tester' | 'coordinator' | 'analyst';
  status: 'idle' | 'busy' | 'error';
  health: number; // 0-100
  cpuUsage: number; // percentage
  memoryUsage: number; // percentage
  createdAt: string; // ISO 8601
  age: number; // milliseconds
}
```

### Communication Object
```typescript
interface Communication {
  id: string;
  type: 'communication';
  timestamp: string; // ISO 8601
  sender: string; // agent ID
  receivers: string[]; // agent IDs
  metadata: {
    size: number; // bytes
    type: string; // communication type
  };
}
```

### Token Usage Object
```typescript
interface TokenUsage {
  total: number;
  byAgent: {
    [agentType: string]: number;
  };
}
```

## Integration Example

```javascript
// VisionFlow Integration Example
class MCPDataSource {
  constructor() {
    this.ws = null;
    this.data = {
      agents: [],
      communications: []
    };
  }

  connect() {
    this.ws = new WebSocket('ws://mcp-orchestrator:9001');

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      switch (message.type) {
        case 'welcome':
        case 'mcp-update':
          this.updateData(message.data);
          this.onDataUpdate(this.data);
          break;
      }
    };

    this.ws.onopen = () => {
      console.log('Connected to MCP Orchestrator');
    };
  }

  updateData(newData) {
    this.data.agents = newData.agents;
    this.data.communications = newData.communications;
  }

  onDataUpdate(data) {
    // Override this method to handle data updates
    // Update force-directed graph nodes and edges
  }
}
```

## Docker Network Configuration

When running in Docker, ensure containers are on the same network:

```yaml
networks:
  powerdev-net:
    external: true
```

Container hostnames:
- Main container: `powerdev-main`
- Orchestrator: `mcp-orchestrator` or `powerdev-mcp-orchestrator`

## Rate Limits

- REST API: 100 requests per 15 minutes per IP
- WebSocket: No rate limits, but clients should implement exponential backoff for reconnections
- Polling interval: 5 seconds (configurable via POLL_INTERVAL env var)

## Error Handling

All errors follow this format:
```json
{
  "error": {
    "code": "TOOL_NOT_FOUND",
    "message": "Unknown MCP tool: invalid/tool",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

Common error codes:
- `CONNECTION_TIMEOUT` - MCP server not responding
- `TOOL_NOT_FOUND` - Invalid tool name
- `INVALID_PARAMS` - Invalid parameters for tool
- `RATE_LIMIT_EXCEEDED` - Too many requests