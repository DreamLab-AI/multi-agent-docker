#!/bin/bash
set -e

echo "--- DEBUG: Checking environment variables ---"
echo "REMOTE_MCP_HOST='${REMOTE_MCP_HOST}'"
echo "-------------------------------------------"

echo "=== MCP 3D Environment Starting ==="
echo "Container IP: $(hostname -I | awk '{print $1}')"
echo "Available MCP Servers: Blender (9876), Revit (8080), Unreal (55557)"
echo ""

# Function to wait for port availability
wait_for_port() {
    local host=$1
    local port=$2
    local timeout=${3:-30}
    local elapsed=0

    echo "Waiting for $host:$port to be available..."
    while ! nc -z "$host" "$port" 2>/dev/null; do
        if [ $elapsed -ge $timeout ]; then
            echo "Timeout waiting for $host:$port"
            return 1
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done
    echo "$host:$port is ready!"
    return 0
}

# Start X Virtual Framebuffer for GUI applications (headless)
echo "--- Starting X Virtual Framebuffer ---"
rm -f /tmp/.X99-lock
Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
export DISPLAY=:99
sleep 2

# Initialize Claude Flow and Ruv Swarm
echo "--- Initializing Claude Flow and Ruv Swarm ---"
if [ ! -f "/home/dev/.claude-flow-initialized" ]; then
    tmux new-session -d -s claude-flow-init 'npx claude-flow@alpha init --force --hive-mind --neural-enhanced && npx claude-flow@alpha mcp setup --auto-permissions --87-tools && claude --dangerously-skip-permissions || true'
    touch /home/dev/.claude-flow-initialized
fi

if [ ! -f "/home/dev/.ruv-swarm-initialized" ]; then
    tmux new-session -d -s ruv-swarm-init 'ruv-swarm || true'
    touch /home/dev/.ruv-swarm-initialized
fi

# Start MCP Servers
echo "--- Starting MCP Servers ---"

# Start Blender MCP Server with proper network binding
# echo "Starting Blender MCP Server on port 9876..."
# tmux new-session -d -s blender-mcp "
#     ${BLENDER_PATH}/blender \
#         --background \
#         --python /app/keep_alive.py \
#         -- \
#         --blendermcp-autostart \
#         --blendermcp-port 9876 \
#         --blendermcp-host 0.0.0.0 \
#         2>&1 | tee /app/mcp-logs/blender-mcp.log
# "

# Start Revit MCP Server
echo "Starting Revit MCP Server on port 8080..."
tmux new-session -d -s revit-mcp "
    cd /app/revit-mcp && \
    PORT=8080 HOST=0.0.0.0 node build/index.js \
    2>&1 | tee /app/mcp-logs/revit-mcp.log
"

# Start Unreal MCP Server
echo "Starting Unreal MCP Server on port 55557..."
tmux new-session -d -s unreal-mcp "
    cd /app/unreal-mcp-source/Python && \
    UNREAL_HOST=0.0.0.0 UNREAL_PORT=55557 /opt/venv312/bin/python unreal_mcp_server.py \
    2>&1 | tee /app/mcp-logs/unreal-mcp.log
"

# Wait for all MCP servers to be ready
echo "--- Waiting for MCP Servers to be ready ---"
MCP_HOST=${REMOTE_MCP_HOST:-localhost}
wait_for_port $MCP_HOST 9876 60   || echo "Warning: Blender MCP server not found at $MCP_HOST:9876. Continuing..."
wait_for_port $MCP_HOST 8080 30   || echo "Warning: Revit MCP server not found at $MCP_HOST:8080. Continuing..."
wait_for_port $MCP_HOST 55557 30  || echo "Warning: Unreal MCP server not found at $MCP_HOST:55557. Continuing..."

# Configure Claude Code MCP settings
echo "--- Configuring Claude Code MCP Settings ---"
mkdir -p /home/dev/.claude
cat > /home/dev/.claude/settings.json << 'EOF'
{
  "mcpServers": {
    "blender": {
      "command": "uvx",
      "args": ["blender-mcp"],
      "env": {
        "BLENDER_HOST": "localhost",
        "BLENDER_PORT": "9876"
      }
    },
    "blender-tcp": {
      "_comment": "Alternative TCP connection method",
      "transport": "tcp",
      "host": "localhost",
      "port": 9876
    },
    "revit": {
      "command": "node",
      "args": ["/app/revit-mcp/build/index.js"],
      "env": {
        "PORT": "8080",
        "HOST": "localhost"
      }
    },
    "unreal": {
      "command": "uv",
      "args": [
        "--directory",
        "/app/unreal-mcp-source/Python",
        "run",
        "unreal_mcp_server.py"
      ],
      "env": {
        "UNREAL_HOST": "localhost",
        "UNREAL_PORT": "55557"
      }
    },
    "ruv-swarm": {
      "command": "npx",
      "args": ["ruv-swarm", "mcp", "start"]
    },
    "claude-flow": {
      "command": "npx",
      "args": ["claude-flow@alpha", "mcp", "start"]
    }
  }
}
EOF

echo "--- Blender MCP process started in the background ---"


# Create helpful aliases for MCP management
cat >> /home/dev/.bashrc << 'EOF'

# MCP Server Management Aliases
alias mcp-status='tmux ls 2>/dev/null || echo "No tmux sessions running"'
alias mcp-logs='tail -f /app/mcp-logs/*.log'
alias mcp-test-blender='nc -zv localhost 9876 && echo "✅ Blender MCP is accessible" || echo "❌ Blender MCP is not accessible"'
alias mcp-test-revit='nc -zv localhost 8080 && echo "✅ Revit MCP is accessible" || echo "❌ Revit MCP is not accessible"'
alias mcp-test-unreal='nc -zv localhost 55557 && echo "✅ Unreal MCP is accessible" || echo "❌ Unreal MCP is not accessible"'
alias mcp-test-all='echo "Testing all MCP servers..."; mcp-test-blender; mcp-test-revit; mcp-test-unreal'

# Quick server access
alias blender-log='tmux attach-session -t blender-mcp'
alias revit-log='tmux attach-session -t revit-mcp'
alias unreal-log='tmux attach-session -t unreal-mcp'


# Network debugging
alias mcp-netstat='netstat -tuln | grep -E "(9876|8080|55557)"'
alias mcp-ports='lsof -i :9876,8080,55557 2>/dev/null || echo "No MCP ports in use"'

echo ""
echo "🚀 MCP 3D Environment Ready!"
echo ""
echo "MCP Server Status:"
mcp-test-all
echo ""
echo "Quick Commands:"
echo "  mcp-status    - Check all server status"
echo "  mcp-logs      - View all server logs"
echo "  mcp-test-all  - Test all MCP connections"
echo ""
EOF

# Print startup information
echo ""
echo "=== MCP 3D Environment Ready ==="
echo ""
echo "MCP Servers (accessible from host):"
echo "  - Blender MCP: localhost:9876"
echo "  - Revit MCP: localhost:8080"
echo "  - Unreal MCP: localhost:55557"
echo ""


echo "Network Information:"
echo "  - Container IP: $(hostname -I | awk '{print $1}')"
echo "  - Bridge Network: 172.20.0.0/16"
echo "  - From container to host: host.docker.internal or host-gateway"
echo "  - From host to container: localhost:PORT"
echo ""

echo "Management:"
echo "  - Run 'mcp-status' to check server status"
echo "  - Run 'mcp-logs' to view logs"
echo "  - Run 'tmux ls' to see background sessions"
echo ""

# First run logic for interactive session
FIRST_RUN_MARKER="/home/dev/.first_run_complete"
if [ ! -f "$FIRST_RUN_MARKER" ] && [ "$1" = "--interactive" ]; then
    echo "--- First run: setting up Claude login ---"
    touch "$FIRST_RUN_MARKER"
    # Try to login to Claude (may fail if already logged in)
    claude login 2>/dev/null || true
fi

# Start appropriate process based on command
if [ "$1" = "--interactive" ]; then
    echo "--- Starting interactive shell ---"
    exec bash -l
else
    echo "--- Running command: $@ ---"
    exec "$@"
fi