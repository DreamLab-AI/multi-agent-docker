#!/bin/bash
set -e

echo "=== MCP 3D Environment Starting ==="
echo "Container IP: $(hostname -I)"
echo "Available MCP Servers: Blender (9876), Revit (8080), Unreal (55557)"
echo ""

# Function to wait for port
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

# Start X Virtual Framebuffer
echo "--- Starting X Virtual Framebuffer ---"
Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
export DISPLAY=:99
sleep 2

# Initialize Claude Flow and Ruv Swarm
echo "--- Initializing Claude Flow and Ruv Swarm ---"
if [ ! -f "/home/dev/.claude-flow-initialized" ]; then
    npx claude-flow@alpha init --force --hive-mind --neural-enhanced  mcp setup --auto-permissions --87-tools || true
    touch /home/dev/.claude-flow-initialized
fi

if [ ! -f "/home/dev/.ruv-swarm-initialized" ]; then
    npx ruv-swarm@latest init --claude || true
    touch /home/dev/.ruv-swarm-initialized
fi

# Start MCP Servers using supervisor
echo "--- Starting MCP Servers with Supervisor ---"
supervisord -c /etc/supervisor/conf.d/supervisord.conf &
SUPERVISOR_PID=$!

# Wait for supervisor to start
sleep 5

# Start Blender with MCP addon
# echo "--- Starting Blender with MCP Server ---"
# tmux new-session -d -s blender-mcp "
#     ${BLENDER_PATH}/blender \
#         --background \
#         --python /app/keep_alive.py \
#         -- \
#         --blendermcp-autostart \
#         --blendermcp-port 9876 \
#         --blendermcp-host 0.0.0.0
# "

# Start Revit MCP Server
echo "--- Starting Revit MCP Server ---"
tmux new-session -d -s revit-mcp "
    cd /app/revit-mcp && \
    PORT=8080 node build/index.js
"

# Start Unreal MCP Server
echo "--- Starting Unreal MCP Server ---"
tmux new-session -d -s unreal-mcp "
    cd /app/unreal-mcp-source/Python && \
    UNREAL_HOST=0.0.0.0 UNREAL_PORT=55557 /opt/venv312/bin/python unreal_mcp_server.py
"

# Wait for all servers to be ready
echo "--- Waiting for MCP Servers to be ready ---"
MCP_HOST=${REMOTE_MCP_HOST:-localhost}
wait_for_port $MCP_HOST 9876 60   || echo "Warning: Blender MCP server not found at $MCP_HOST:9876. Continuing..."
wait_for_port $MCP_HOST 8080 30   || echo "Warning: Revit MCP server not found at $MCP_HOST:8080. Continuing..."
wait_for_port $MCP_HOST 55557 30  || echo "Warning: Unreal MCP server not found at $MCP_HOST:55557. Continuing..."

# Configure Claude Code MCP settings
echo "--- Configuring Claude Code MCP Settings ---"
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
    "revit": {
      "command": "node",
      "args": ["/app/revit-mcp/build/index.js"],
      "env": {
        "PORT": "8080"
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

# Create helpful aliases
cat >> /home/dev/.bashrc << 'EOF'

# MCP Server Management
alias mcp-status='supervisorctl status'
alias mcp-restart='supervisorctl restart all'
alias mcp-logs='tail -f /app/mcp-logs/*.log'
alias mcp-test-blender='nc -zv localhost 9876'
alias mcp-test-revit='nc -zv localhost 8080'
alias mcp-test-unreal='nc -zv localhost 55557'
alias mcp-tmux-list='tmux ls'
alias mcp-tmux-attach='tmux attach-session -t'

# Quick server access
alias blender-log='tmux attach-session -t blender-mcp'
alias revit-log='tmux attach-session -t revit-mcp'
alias unreal-log='tmux attach-session -t unreal-mcp'


echo "MCP 3D Environment Ready!"
echo "Run 'mcp-status' to check server status"
EOF

# Print connection information
echo ""
echo "=== MCP 3D Environment Ready ==="
echo "MCP Servers:"
echo "  - Blender MCP: localhost:9876 (or host.docker.internal:9876 from host)"
echo "  - Revit MCP: localhost:8080 (or host.docker.internal:8080 from host)"
echo "  - Unreal MCP: localhost:55557 (or host.docker.internal:55557 from host)"
echo ""
echo "Management:"
echo "  - Run 'mcp-status' to check server status"
echo "  - Run 'mcp-logs' to view logs"
echo "  - Run 'tmux ls' to see background sessions"
echo ""

# Handle first run vs subsequent runs
FIRST_RUN_MARKER="/home/dev/.first_run_complete"
if [ ! -f "$FIRST_RUN_MARKER" ] && [ "$1" = "--interactive" ]; then
    echo "--- First run: setting up Claude login ---"
    touch "$FIRST_RUN_MARKER"
    claude login || true
fi

# Start appropriate process based on command
if [ "$1" = "--interactive" ]; then
    echo "--- Starting interactive shell ---"
    exec bash -l
else
    echo "--- Running command: $@ ---"
    exec "$@"
fi