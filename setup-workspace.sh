#!/bin/bash
# Enhanced setup script that includes MCP TCP server installation
# This replaces or augments the existing setup-workspace.sh

set -e

echo "🚀 Initializing enhanced PowerDev workspace with TCP/Unix MCP support..."

# 1. Run original setup if exists
if [ -f "/app/setup-workspace-original.sh" ]; then
    echo "📦 Running original setup..."
    /app/setup-workspace-original.sh "$@"
fi

# 2. Copy essential assets and helpers (if not already done)
if [ ! -f "./mcp-helper.sh" ]; then
    echo "📂 Copying essential assets and helper scripts into workspace..."
    mkdir -p ./mcp-tools/ ./scripts/
    cp -r /app/core-assets/mcp-tools/. ./mcp-tools/ 2>/dev/null || true
    cp -r /app/core-assets/scripts/. ./scripts/ 2>/dev/null || true
    cp /app/core-assets/mcp.json ./.mcp.json 2>/dev/null || true
    cp /app/mcp-helper.sh ./ 2>/dev/null || true
    chmod +x ./mcp-helper.sh 2>/dev/null || true
fi

# 3. Install MCP TCP Server wrapper
echo "--------------------------------------------------"
echo "🔌 Installing MCP TCP/Unix server wrapper..."

# Create directories
mkdir -p /var/run/mcp
mkdir -p /app/mcp-logs

# Copy the TCP server wrapper
if [ -f "/app/patches/mcp-tcp-server.js" ]; then
    cp /app/patches/mcp-tcp-server.js /app/mcp-tcp-server.js
    chmod +x /app/mcp-tcp-server.js
    echo "✅ MCP TCP server wrapper installed"
fi

# 4. Create systemd-style service script (if systemd not available)
echo "🎯 Creating MCP TCP service launcher..."
cat > /app/start-mcp-tcp.sh << 'EOF'
#!/bin/bash
# Start MCP TCP Server

# Source environment
export MCP_TCP_PORT="${MCP_TCP_PORT:-9500}"
export MCP_ENABLE_TCP="${MCP_ENABLE_TCP:-true}"
export MCP_ENABLE_UNIX="${MCP_ENABLE_UNIX:-false}"
export MCP_LOG_LEVEL="${MCP_LOG_LEVEL:-info}"

# Check if already running
if [ -f "/var/run/mcp-tcp.pid" ]; then
    PID=$(cat /var/run/mcp-tcp.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "MCP TCP server already running (PID: $PID)"
        exit 0
    fi
fi

# Start the server
echo "Starting MCP TCP server on port $MCP_TCP_PORT..."
nohup node /app/mcp-tcp-server.js > /app/mcp-logs/tcp-server.log 2>&1 &
echo $! > /var/run/mcp-tcp.pid
echo "MCP TCP server started (PID: $!)"
EOF
chmod +x /app/start-mcp-tcp.sh

# 5. Create stop script
cat > /app/stop-mcp-tcp.sh << 'EOF'
#!/bin/bash
# Stop MCP TCP Server

if [ -f "/var/run/mcp-tcp.pid" ]; then
    PID=$(cat /var/run/mcp-tcp.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "Stopping MCP TCP server (PID: $PID)..."
        kill $PID
        rm /var/run/mcp-tcp.pid
        echo "MCP TCP server stopped"
    else
        echo "MCP TCP server not running"
        rm /var/run/mcp-tcp.pid
    fi
else
    echo "MCP TCP server not running (no PID file)"
fi
EOF
chmod +x /app/stop-mcp-tcp.sh

# 6. Create status script
cat > /app/status-mcp-tcp.sh << 'EOF'
#!/bin/bash
# Check MCP TCP Server status

if [ -f "/var/run/mcp-tcp.pid" ]; then
    PID=$(cat /var/run/mcp-tcp.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ MCP TCP server is running (PID: $PID)"
        echo "   Port: ${MCP_TCP_PORT:-9500}"
        
        # Check if port is listening
        if netstat -tuln | grep -q ":${MCP_TCP_PORT:-9500}"; then
            echo "   Status: Listening on port ${MCP_TCP_PORT:-9500}"
        else
            echo "   Status: Process running but port not listening"
        fi
        
        # Get health check if available
        if curl -s http://127.0.0.1:9501/health 2>/dev/null; then
            echo ""
        fi
    else
        echo "❌ MCP TCP server is not running (stale PID file)"
        rm /var/run/mcp-tcp.pid
    fi
else
    echo "❌ MCP TCP server is not running"
fi
EOF
chmod +x /app/status-mcp-tcp.sh

# 7. Auto-start TCP server if enabled
if [ "${MCP_TCP_AUTOSTART}" = "true" ] || [ "${MCP_ENABLE_TCP}" = "true" ]; then
    echo "🚀 Auto-starting MCP TCP server..."
    /app/start-mcp-tcp.sh
fi

# 8. Update bashrc with new aliases
if [ -f "/home/dev/.bashrc" ]; then
    # Check if aliases already added
    if ! grep -q "mcp-tcp-start" /home/dev/.bashrc; then
        cat >> /home/dev/.bashrc << 'EOF'

# MCP TCP Server Management
alias mcp-tcp-start='/app/start-mcp-tcp.sh'
alias mcp-tcp-stop='/app/stop-mcp-tcp.sh'
alias mcp-tcp-status='/app/status-mcp-tcp.sh'
alias mcp-tcp-restart='/app/stop-mcp-tcp.sh && /app/start-mcp-tcp.sh'
alias mcp-tcp-logs='tail -f /app/mcp-logs/tcp-server.log'
alias mcp-tcp-test='echo "{\"jsonrpc\":\"2.0\",\"id\":\"1\",\"method\":\"initialize\",\"params\":{}}" | nc localhost ${MCP_TCP_PORT:-9500}'

# Quick TCP connection test
mcp-test-tcp() {
    local port=${1:-9500}
    echo "Testing MCP TCP connection on port $port..."
    echo '{"jsonrpc":"2.0","id":"test","method":"tools/list","params":{}}' | nc -w 2 localhost $port
}
EOF
        echo "✅ TCP server aliases added to bashrc"
    fi
fi

# 9. Create a simple test client
cat > /app/test-mcp-tcp.js << 'EOF'
#!/usr/bin/env node
// Simple test client for MCP TCP server

const net = require('net');

const port = process.env.MCP_TCP_PORT || 9500;
const client = net.createConnection({ port, host: 'localhost' }, () => {
    console.log('Connected to MCP TCP server');
    
    // Send initialization request
    const init = {
        jsonrpc: '2.0',
        id: 'init-1',
        method: 'initialize',
        params: {
            protocolVersion: '2024-11-05',
            capabilities: { tools: { listChanged: true } },
            clientInfo: { name: 'test-client', version: '1.0.0' }
        }
    };
    
    client.write(JSON.stringify(init) + '\n');
});

client.on('data', (data) => {
    console.log('Received:', data.toString());
    
    // After init, list tools
    const list = {
        jsonrpc: '2.0',
        id: 'list-1',
        method: 'tools/list',
        params: {}
    };
    
    setTimeout(() => {
        client.write(JSON.stringify(list) + '\n');
        setTimeout(() => client.end(), 1000);
    }, 100);
});

client.on('end', () => {
    console.log('Disconnected from server');
    process.exit(0);
});

client.on('error', (err) => {
    console.error('Connection error:', err.message);
    process.exit(1);
});
EOF
chmod +x /app/test-mcp-tcp.js

# 10. Update CLAUDE.md with TCP server info
if [ -f "./CLAUDE.md" ]; then
    if ! grep -q "MCP TCP Server" ./CLAUDE.md; then
        cat >> ./CLAUDE.md << 'EOF'

## 🔌 MCP TCP Server

A TCP server is available for direct MCP connections on port 9500 (configurable via MCP_TCP_PORT).

### Usage from external containers:
```javascript
const net = require('net');
const client = net.connect(9500, 'multi-agent-container');
// Send JSON-RPC requests, receive responses
```

### Management commands:
- `mcp-tcp-start` - Start the TCP server
- `mcp-tcp-stop` - Stop the TCP server
- `mcp-tcp-status` - Check server status
- `mcp-tcp-logs` - View server logs
- `mcp-test-tcp` - Test TCP connection

### Environment variables:
- `MCP_TCP_PORT=9500` - TCP server port
- `MCP_ENABLE_TCP=true` - Enable TCP server
- `MCP_ENABLE_UNIX=false` - Enable Unix socket
- `MCP_LOG_LEVEL=info` - Log verbosity (debug|info|warn|error)
EOF
        echo "✅ CLAUDE.md updated with TCP server information"
    fi
fi

# 11. Final status check
echo ""
echo "=== MCP Enhanced Setup Complete ==="
echo ""
/app/status-mcp-tcp.sh
echo ""
echo "TCP Server Management:"
echo "  Start:   mcp-tcp-start"
echo "  Stop:    mcp-tcp-stop"
echo "  Status:  mcp-tcp-status"
echo "  Logs:    mcp-tcp-logs"
echo "  Test:    node /app/test-mcp-tcp.js"
echo ""
echo "External containers can now connect to:"
echo "  TCP:       multi-agent-container:${MCP_TCP_PORT:-9500}"
echo "  WebSocket: multi-agent-container:3002 (existing)"
echo ""