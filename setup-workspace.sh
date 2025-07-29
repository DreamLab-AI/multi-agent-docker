#!/bin/bash
# Unified setup script for a fresh PowerDev workspace.

set -e
echo "🚀 Initializing new PowerDev workspace..."

# 1. Check if workspace is already initialized
if [ -d ".claude" ] && [ "$1" != "--force" ]; then
    echo "⚠️ Workspace appears to be already set up. Use --force to re-initialize."
    exit 0
fi

# 2. Copy core assets from the image into the workspace
echo "📂 Copying core assets into workspace..."
cp -r /app/core-assets/claude-config/. ./.claude/
cp -r /app/core-assets/roo-config/. ./.roo/
cp -r /app/mcp-tools/. ./mcp-tools/
cp /app/core-assets/scripts/mcp-blender-client.js .
cp /app/core-assets/mcp.json ./.mcp.json
echo "✅ Core assets copied."

# 3. Interactively initialize claude-flow
echo "--------------------------------------------------"
echo "🤖 Starting Claude Flow initialization..."
echo "This will set up your agent environment."
npx claude-flow@alpha init --force --hive-mind --neural-enhanced

# 4. Set up MCP tools within claude-flow
echo "--------------------------------------------------"
echo "🛠️ Setting up MCP tools..."
npx claude-flow@alpha mcp setup --auto-permissions --87-tools

# 5. Initialize MCP servers based on the copied .mcp.json
echo "--------------------------------------------------"
echo "🔌 Initializing MCP servers from .mcp.json..."
npx claude-flow@alpha mcp init --file ./.mcp.json

echo "--------------------------------------------------"
echo "🎉 Workspace setup complete!"
echo
echo "Next Steps:"
echo "1. Grant permissions for this session:"
echo "   claude --dangerously-skip-permissions"
echo
echo "2. Your custom MCP tools are now in ./mcp-tools/ and can be edited."
echo "   The MCP server configuration is in ./.mcp.json."
echo
echo "You are ready to start working with Claude."
echo "--------------------------------------------------"