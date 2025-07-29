#!/bin/bash
# Unified setup script for a fresh PowerDev workspace.

set -e
echo "🚀 Initializing new PowerDev workspace..."

# 1. Check if workspace is already initialized
if [ -d ".claude" ] && [ "$1" != "--force" ]; then
    echo "⚠️ Workspace appears to be already set up. Use --force to re-initialize."
    exit 0
fi

# 2. Copy essential assets from the image into the workspace
echo "📂 Copying essential assets into workspace..."
cp -r /app/core-assets/mcp-tools/. ./mcp-tools/
cp -r /app/core-assets/scripts/. ./scripts/
cp /app/core-assets/mcp.json ./.mcp.json
echo "✅ Essential assets copied."

# 3. Install and initialize claude-flow
echo "--------------------------------------------------"
echo "📦 Installing claude-flow locally..."
npm install claude-flow@alpha
echo "🚀 Starting Claude Flow initialization..."
echo "This will set up your agent environment."
./node_modules/.bin/claude-flow init --force --hive-mind --neural-enhanced

# 4. Initialize MCP servers based on the copied .mcp.json
echo "--------------------------------------------------"
echo "🔌 Initializing MCP servers from .mcp.json..."
./node_modules/.bin/claude-flow mcp init --file ./.mcp.json || true

# 5. Verify MCP servers are ready
echo "--------------------------------------------------"
echo "🔗 Verifying MCP servers and tools..."
echo "Checking supervisord background services..."
supervisorctl -c /etc/supervisor/conf.d/supervisord.conf status || echo "ℹ️  Supervisord may not be running yet. Start it with: sudo supervisord -c /etc/supervisor/conf.d/supervisord.conf"

echo ""
echo "Checking claude-flow tool availability..."
# Use claude-flow to list tools and check if our key tools are registered.
if ./node_modules/.bin/claude-flow mcp tools | grep -q "blender-mcp"; then
    echo "✅ Blender MCP tool is registered with claude-flow."
else
    echo "⚠️ Blender MCP tool is NOT registered. Check .mcp.json."
fi

if ./node_modules/.bin/claude-flow mcp tools | grep -q "qgis-mcp"; then
    echo "✅ QGIS MCP tool is registered with claude-flow."
else
    echo "⚠️ QGIS MCP tool is NOT registered. Check .mcp.json."
fi

echo ""
echo "💡 For these tools to work, ensure the external Blender and QGIS applications"
echo "   with their MCP server plugins are running and accessible from the container."

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