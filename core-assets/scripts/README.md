# MCP Server Scripts

This directory contains the core scripts for running the Multi-Agent Docker MCP (Model Context Protocol) servers with enhanced security features.

## Files

### Core Servers

#### `mcp-tcp-server.js`
- Persistent TCP server for MCP connections
- Maintains single MCP instance across all connections
- Enhanced with authentication and security features
- Default port: 9500

#### `mcp-ws-relay.js`
- WebSocket to MCP bridge server
- Provides WebSocket interface for browser-based clients
- Enhanced with token authentication and rate limiting
- Default port: 3002

#### `mcp-server.js`
- Main MCP server implementation
- Handles tool execution and agent coordination

#### `mcp-blender-client.js`
- Specialized client for Blender integration
- Connects to the Blender GUI service

### Security Components

#### `auth-middleware.js`
- Authentication and authorization middleware
- Rate limiting implementation
- Input validation and sanitization
- IP blocking and connection management
- Security event logging

## Security Features

### Authentication
- **Token-based authentication** for WebSocket connections
- **JWT support** for API authentication
- **Session management** with configurable timeouts

### Rate Limiting
- **Per-IP rate limiting** to prevent abuse
- **Configurable time windows** and request limits
- **Automatic IP blocking** for violations

### Input Validation
- **Size limits** on requests (default: 10MB)
- **JSON-RPC validation** for protocol compliance
- **Content sanitization** to prevent injection attacks
- **Prototype pollution protection**

### Connection Management
- **Maximum connection limits** per server
- **Idle connection timeouts**
- **Graceful connection cleanup**

## Configuration

All security features are configured through environment variables. See `.env.example` for details:

```bash
# Authentication
WS_AUTH_ENABLED=true
WS_AUTH_TOKEN=your-secure-token
JWT_SECRET=your-jwt-secret

# Rate Limiting
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQUESTS=100

# Connection Limits
WS_MAX_CONNECTIONS=100
TCP_MAX_CONNECTIONS=50
```

## Usage

### Starting the Servers

```bash
# TCP Server
node mcp-tcp-server.js

# WebSocket Server
node mcp-ws-relay.js

# With authentication enabled
WS_AUTH_ENABLED=true WS_AUTH_TOKEN=secret123 node mcp-ws-relay.js
```

### Client Connection Examples

#### WebSocket with Authentication
```javascript
const ws = new WebSocket('ws://localhost:3002', {
  headers: {
    'Authorization': 'Bearer your-auth-token'
  }
});
```

#### TCP with Authentication
```javascript
// After connection, send authentication request
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "authenticate",
  "params": {
    "token": "your-auth-token"
  }
}
```

## Security Best Practices

1. **Always enable authentication** in production environments
2. **Use strong, randomly generated tokens** (minimum 32 characters)
3. **Configure appropriate rate limits** based on your use case
4. **Monitor security logs** for suspicious activity
5. **Regularly rotate authentication tokens**
6. **Use HTTPS/WSS** in production deployments
7. **Implement proper firewall rules** to restrict access

## Monitoring

Security events are logged with the `[SECURITY]` prefix:
```
[SECURITY] {"timestamp":"2024-01-01T00:00:00.000Z","event":"invalid_auth","ip":"192.168.1.1"}
```

Monitor these logs for:
- Failed authentication attempts
- Rate limit violations
- Connection limit exceeded events
- Invalid input attempts

## Troubleshooting

### Common Issues

1. **"Unauthorized" errors**
   - Verify `WS_AUTH_TOKEN` is set correctly
   - Check that clients include the token in requests

2. **"Rate limit exceeded" errors**
   - Increase `RATE_LIMIT_MAX_REQUESTS` if needed
   - Check for misbehaving clients

3. **"Service unavailable" errors**
   - Connection limit reached
   - Increase `WS_MAX_CONNECTIONS` or `TCP_MAX_CONNECTIONS`

### Debug Mode

Enable verbose logging:
```bash
MCP_LOG_LEVEL=debug node mcp-tcp-server.js
```

## Migration Guide

If upgrading from a previous version without security:

1. Run the migration script: `node /workspace/ext/scripts/migrate-env.js`
2. Update client code to include authentication
3. Test thoroughly before enabling in production

For more details, see the [Security Documentation](/workspace/ext/docs/SECURITY.md).