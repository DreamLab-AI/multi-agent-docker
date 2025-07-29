#!/bin/bash
set -e

echo "=== MCP 3D Environment Starting ==="
echo "Container IP: $(hostname -I)"

# Start X Virtual Framebuffer
echo "--- Starting X Virtual Framebuffer ---"
Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
export DISPLAY=:99
sleep 2

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
alias mcp-tmux-list='tmux ls'
alias mcp-tmux-attach='tmux attach-session -t'

# Quick server access
alias blender-log='tmux attach-session -t blender-mcp'
alias revit-log='tmux attach-session -t revit-mcp'
alias unreal-log='tmux attach-session -t unreal-mcp'
EOF

# Print connection information
echo ""
echo "=== MCP 3D Environment Ready ==="
echo "This environment connects to external MCP servers."
echo "Blender MCP is expected at ${BLENDER_HOST:-blender-host}:${BLENDER_PORT:-9876} on the docker_ragflow network."
echo ""
echo "To set up a fresh workspace, run the setup script:"
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