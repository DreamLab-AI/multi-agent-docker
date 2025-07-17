#!/bin/bash
set -e

echo "--- Initializing Claude Flow and Ruv Swarm ---"
npx claude-flow@alpha init --force
npx ruv-swarm@latest init --claude
echo "--- Initialization Complete ---"

echo "--- Starting Headless Blender MCP Container in background ---"

# Start Blender in the background
${BLENDER_PATH}/blender \
    --background \
    --python /app/keep_alive.py \
    -- \
    --blendermcp-autostart \
    --blendermcp-port 9876 &

echo "--- Blender MCP process started in the background ---"

# First run logic for interactive session
FIRST_RUN_MARKER="/home/dev/.first_run_complete"
if [ ! -f "$FIRST_RUN_MARKER" ]; then
    echo "--- First run: setting up Claude login in tmux ---"
    touch "$FIRST_RUN_MARKER"
    # Create a detached tmux session, run login, then leave a shell open
    tmux new-session -d -s main "claude --dangerously-skip-permissions; exec bash -l"
    # Attach to the session, making it the main process
    exec tmux attach-session -t main
else
    echo "--- Subsequent run: starting shell ---"
    # On subsequent runs, just start a login shell
    exec bash -l
fi