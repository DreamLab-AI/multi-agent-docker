#!/bin/bash
# Unified setup script for a fresh PowerDev workspace.

set -e

echo "🚀 Initializing new PowerDev workspace..."

# 1. Force re-initialization if --force is used
if [ -f "package.json" ] && [ "$1" != "--force" ]; then
    echo "⚠️ Workspace appears to be already set up. Use --force to re-initialize."
    exit 0
fi

# 2. Copy essential assets and helpers
echo "📂 Copying essential assets and helper scripts into workspace..."
mkdir -p ./mcp-tools/ ./scripts/
cp -r /app/core-assets/mcp-tools/. ./mcp-tools/
cp -r /app/core-assets/scripts/. ./scripts/
cp /app/core-assets/mcp.json ./.mcp.json
cp /app/mcp-helper.sh ./

# Make all scripts executable
echo "🔧 Setting script permissions..."
chmod +x ./mcp-helper.sh
find ./mcp-tools -name "*.py" -exec chmod +x {} \;
find ./scripts -name "*.js" -exec chmod +x {} \;
echo "✅ Assets copied and permissions set."

# 3. Install local Node.js dependencies
echo "--------------------------------------------------"
echo "📦 Installing local Node.js dependencies..."
if [ ! -f "package.json" ]; then
    npm init -y > /dev/null 2>&1
fi
npm install claude-flow@alpha > /dev/null 2>&1
echo "✅ Dependencies installed."

# 4. Update CLAUDE.md with MCP tool knowledge
echo "--------------------------------------------------"
echo "🤖 Appending MCP tool knowledge to CLAUDE.md..."
if [ ! -f "CLAUDE.md" ]; then
    cp /app/AGENT-BRIEFING.md ./CLAUDE.md
fi

MCP_KNOWLEDGE_BLOCK="
## 🛠️ MCP Tools Available

**CRITICAL**: Use \`./mcp-helper.sh list-tools\` and \`./mcp-helper.sh run-tool <tool> '<json>'\`

Available: imagemagick-mcp, blender-mcp, qgis-mcp, kicad-mcp, ngspice-mcp, pbr-generator-mcp
"

if ! grep -q "Multi-Agent Docker MCP Tools" "CLAUDE.md"; then
    echo "$MCP_KNOWLEDGE_BLOCK" >> CLAUDE.md
    echo "✅ Knowledge block added to CLAUDE.md."
else
    echo "✅ Knowledge block already exists in CLAUDE.md."
fi

# 5. Verify the environment is ready
echo "--------------------------------------------------"
echo "🔗 Verifying final environment state..."
echo "Checking supervisord background services..."
if supervisorctl -c /etc/supervisor/conf.d/supervisord.conf status | grep -q 'RUNNING'; then
    echo "✅ Supervisord services are running."
else
    echo "⚠️ Supervisord services are not running correctly. Check logs."
fi

echo ""
echo "Verifying MCP tool availability..."
if ./mcp-helper.sh list-tools &> /dev/null; then
    echo "✅ All MCP tools are registered and accessible via './mcp-helper.sh'."
else
    echo "❌ FAILED: Could not list MCP tools. Please check logs."
fi

echo "--------------------------------------------------"
echo "🎉 Workspace setup complete!"
echo "💡 Use './mcp-helper.sh help' to see available commands."
echo "💡 Check 'CLAUDE.md' for detailed instructions on how to use the tools."
echo "--------------------------------------------------"