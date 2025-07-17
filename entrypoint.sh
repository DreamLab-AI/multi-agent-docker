#!/bin/bash
set -e

echo "--- Starting Headless Blender MCP Container ---"

# The command to start Blender headlessly
# --background: Runs Blender without a GUI.
# --python-use-system-env: Ensures Blender uses the container's Python environment.
# --addons addon: Enables our modified addon.
# --python /app/keep_alive.py: Runs our keep-alive script inside Blender.
# --: Separator for passing arguments to the Python script.
# --blendermcp-autostart: A flag for our script to start the server.
# --blendermcp-port 9876: The port for the MCP server.

${BLENDER_PATH}/blender \
    --background \
    --addons addon \
    --python /app/keep_alive.py \
    -- \
    --blendermcp-autostart \
    --blendermcp-port 9876

echo "--- Blender MCP Container Started ---"