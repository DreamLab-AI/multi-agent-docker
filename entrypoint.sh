#!/bin/bash
set -e

echo "=== MCP 3D Environment Starting ==="
echo "Container IP: $(hostname -I)"

# Ensure the dev user owns the workspace
chown -R dev:dev /workspace

# Ensure the supervisor directory exists
mkdir -p /workspace/.supervisor
# Create helpful aliases if .bashrc exists for the user
if [ -f "/home/dev/.bashrc" ]; then
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
fi

echo ""
echo "=== MCP Environment Ready ==="
echo "Background services are managed by supervisord."
echo "The WebSocket bridge for external control is on port 3002."
echo ""
echo "To set up a fresh workspace, run:"
echo "  /app/setup-workspace.sh"
echo ""

# Execute supervisord as the main process
exec /usr/bin/supervisord -n -c /etc/supervisor/conf.d/supervisord.conf