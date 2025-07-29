#!/bin/bash
set -e

echo "=== MCP 3D Environment Starting ==="
echo "Container IP: $(hostname -I)"

# Ensure the supervisor directory exists
mkdir -p /workspace/.supervisor
# Start MCP Servers using supervisor
echo "--- Starting MCP Servers with Supervisor ---"
supervisord -c /etc/supervisor/conf.d/supervisord.conf &
SUPERVISOR_PID=$!

# Wait for supervisor to start
sleep 2

# Create helpful aliases
cat >> /home/dev/.bashrc << 'EOF'

# MCP Server Management
alias mcp-status='supervisorctl -c /etc/supervisor/conf.d/supervisord.conf status'
alias mcp-restart='supervisorctl -c /etc/supervisor/conf.d/supervisord.conf restart all'
alias mcp-logs='tail -f /app/mcp-logs/*.log'
alias mcp-test-blender='nc -zv localhost 9876'
alias mcp-test-qgis='nc -zv localhost 9877'
alias mcp-blender-status='supervisorctl -c /etc/supervisor/conf.d/supervisord.conf status blender-mcp-server'
alias mcp-qgis-status='supervisorctl -c /etc/supervisor/conf.d/supervisord.conf status qgis-mcp-server'
alias mcp-tmux-list='tmux ls'
alias mcp-tmux-attach='tmux attach-session -t'

# Quick server access
alias blender-log='tail -f /app/mcp-logs/blender-mcp-server.log'
alias qgis-log='tail -f /app/mcp-logs/qgis-mcp-server.log'
EOF

# Print connection information
echo ""
echo "=== MCP Environment Ready ==="
echo "Background services managed by supervisord:"
supervisorctl -c /etc/supervisor/conf.d/supervisord.conf status || echo "ℹ️  Supervisord is starting..."
echo ""
echo "MCP tools are managed by claude-flow and connect to external applications."
echo "The WebSocket bridge for external control is on port 3002."
echo ""
echo "To set up a fresh workspace, run:"
echo "  /app/setup-workspace.sh"

# Start appropriate process based on command
if [ "$1" = "--interactive" ]; then
    echo "--- Starting interactive shell ---"
    # Check if workspace is empty and print a hint
    if [ -z "$(ls -A /workspace)" ]; then
        echo "💡 Your workspace is empty. Run '/app/setup-workspace.sh' to initialize it."
    fi
    exec bash -l
else
    echo "--- Running command: $@ ---"
    exec "$@"
fi