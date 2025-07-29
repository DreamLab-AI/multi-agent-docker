#!/bin/bash
set -e

# Source all profile scripts to ensure environment variables are loaded
for f in /etc/profile.d/*.sh; do source "$f"; done

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
alias mcp-test-revit='nc -zv localhost 8080'
alias mcp-test-unreal='nc -zv localhost 55557'
alias mcp-test-qgis='nc -zv localhost 9877'
alias mcp-blender-status='supervisorctl -c /etc/supervisor/conf.d/supervisord.conf status blender-mcp-server'
alias mcp-qgis-status='supervisorctl -c /etc/supervisor/conf.d/supervisord.conf status qgis-mcp-server'
alias mcp-unreal-status='supervisorctl -c /etc/supervisor/conf.d/supervisord.conf status unreal-mcp'
alias mcp-revit-status='supervisorctl -c /etc/supervisor/conf.d/supervisord.conf status revit-mcp'
alias mcp-tmux-list='tmux ls'
alias mcp-tmux-attach='tmux attach-session -t'

# Quick server access
alias blender-log='tail -f /app/mcp-logs/blender-mcp-server.log'
alias qgis-log='tail -f /app/mcp-logs/qgis-mcp-server.log'
alias revit-log='tail -f /app/mcp-logs/revit-mcp.log'
alias unreal-log='tail -f /app/mcp-logs/unreal-mcp.log'
EOF

# Print connection information
echo ""
echo "=== MCP 3D Environment Ready ==="
echo "This environment manages MCP tools via claude-flow."
echo "Background services managed by supervisord:"
supervisorctl -c /etc/supervisor/conf.d/supervisord.conf status || echo "ℹ️  Supervisord is starting..."
echo ""
echo "MCP tools are managed by claude-flow and connect to external applications:"
echo "  - Blender tool expects external Blender at port 9876"
echo "  - QGIS tool expects external QGIS at port 9877"
echo ""
echo "To set up a fresh workspace, run the setup script:"
echo "  /app/setup-workspace.sh"
echo ""
echo "To use the locally installed claude-flow, run:"
echo "  ./node_modules/.bin/claude-flow"

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