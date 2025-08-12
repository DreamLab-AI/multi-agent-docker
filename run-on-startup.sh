#!/bin/bash
set -e

# 1. Initialize Workspace
if [ ! -f "/workspace/.workspace-initialized" ]; then
    echo "First time setup. Initializing workspace..."
    /app/setup-workspace.sh --force
    touch /workspace/.workspace-initialized
    chown dev:dev /workspace/.workspace-initialized
fi

# 3. Final Entrypoint Logic
echo "Starting supervisord..."
exec /usr/bin/supervisord -n -c /etc/supervisor/conf.d/supervisord.conf