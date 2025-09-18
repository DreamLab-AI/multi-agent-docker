#!/bin/bash
set -e

echo "=== MCP 3D Environment Starting ==="
echo "Container IP: $(hostname -I)"

# Security initialization
echo "=== Security Initialization ==="

# Check if security tokens are set
if [ -z "$WS_AUTH_TOKEN" ] || [ "$WS_AUTH_TOKEN" = "your-secure-websocket-token-change-me" ]; then
    echo "⚠️  WARNING: Default WebSocket auth token detected. Please update WS_AUTH_TOKEN in .env"
fi

if [ -z "$TCP_AUTH_TOKEN" ] || [ "$TCP_AUTH_TOKEN" = "your-secure-tcp-token-change-me" ]; then
    echo "⚠️  WARNING: Default TCP auth token detected. Please update TCP_AUTH_TOKEN in .env"
fi

if [ -z "$JWT_SECRET" ] || [ "$JWT_SECRET" = "your-super-secret-jwt-key-minimum-32-chars" ]; then
    echo "⚠️  WARNING: Default JWT secret detected. Please update JWT_SECRET in .env"
fi

# Create security log directory
mkdir -p /app/mcp-logs/security
chown -R dev:dev /app/mcp-logs

# Set secure permissions on scripts
chmod 750 /app/core-assets/scripts/*.js
chown dev:dev /app/core-assets/scripts/*.js

echo "✅ Security initialization complete"

# Ensure the dev user owns their home directory to prevent permission
# issues with npx, cargo, etc. This is safe to run on every start.
chown -R dev:dev /home/dev

# Fix claude installation path issue - installer may use /home/ubuntu
if [ -f /home/ubuntu/.local/bin/claude ] && [ ! -f /usr/local/bin/claude ]; then
    ln -sf /home/ubuntu/.local/bin/claude /usr/local/bin/claude
    chmod +x /usr/local/bin/claude 2>/dev/null || true
    echo "✅ Created claude symlink from ubuntu home"
fi

# The dev user inside the container is created with the same UID/GID as the
# host user, so a recursive chown on /workspace is not necessary and can
# cause permission errors on bind mounts.

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
alias mcp-test-tcp='nc -zv localhost 9500'
alias mcp-test-ws='nc -zv localhost 3002'
alias mcp-blender-status='supervisorctl -c /etc/supervisor/conf.d/supervisord.conf status blender-mcp-server'
alias mcp-qgis-status='supervisorctl -c /etc/supervisor/conf.d/supervisord.conf status qgis-mcp-server'
alias mcp-tcp-status='supervisorctl -c /etc/supervisor/conf.d/supervisord.conf status mcp-tcp-server'
alias mcp-ws-status='supervisorctl -c /etc/supervisor/conf.d/supervisord.conf status mcp-ws-bridge'
alias mcp-tmux-list='tmux ls'
alias mcp-tmux-attach='tmux attach-session -t'

# Quick server access
alias blender-log='tail -f /app/mcp-logs/blender-mcp-server.log'
alias qgis-log='tail -f /app/mcp-logs/qgis-mcp-server.log'
alias tcp-log='tail -f /app/mcp-logs/mcp-tcp-server.log'
alias ws-log='tail -f /app/mcp-logs/mcp-ws-bridge.log'

# Security and monitoring
alias mcp-health='curl -f http://localhost:9501/health'
alias mcp-security-audit='grep SECURITY /app/mcp-logs/*.log | tail -20'
alias mcp-connections='ss -tulnp | grep -E ":(3002|9500|9876|9877)"'
alias mcp-secure-client='node /app/core-assets/scripts/secure-client-example.js'

# Claude shortcuts
alias dsp='claude --dangerously-skip-permissions'

# Performance monitoring
alias mcp-performance='top -p $(pgrep -f "node.*mcp")'
alias mcp-memory='ps aux | grep -E "node.*mcp" | awk "{print \$1,\$2,\$4,\$6,\$11}"'
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