#!/bin/bash
# MCP Server Initialization Script
# This script initializes and configures all MCP servers for the multi-agent Docker environment

set -e

echo "======================================"
echo "MCP Server Initialization"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to test MCP server
test_mcp_server() {
    local server_name=$1
    local test_command=$2

    echo -e "${YELLOW}Testing ${server_name}...${NC}"
    if eval "$test_command" 2>/dev/null; then
        echo -e "${GREEN}✓ ${server_name} is working${NC}"
        return 0
    else
        echo -e "${RED}✗ ${server_name} failed to respond${NC}"
        return 1
    fi
}

# Ensure we're in the workspace directory
cd /workspace || exit 1

# Step 1: Install/Update MCP servers
echo -e "\n${YELLOW}Step 1: Installing/Updating MCP servers...${NC}"

# Install Claude Flow
echo "Installing Claude Flow..."
npm install -g claude-flow@alpha --force || {
    echo -e "${RED}Failed to install Claude Flow${NC}"
    exit 1
}

# Install Ruv Swarm
echo "Installing Ruv Swarm..."
npm install -g ruv-swarm@latest --force || {
    echo -e "${RED}Failed to install Ruv Swarm${NC}"
    exit 1
}

# Step 2: Configure MCP settings
echo -e "\n${YELLOW}Step 2: Configuring MCP settings...${NC}"

# Ensure .claude directory exists
mkdir -p /workspace/.claude

# Copy MCP configuration
if [ -f "/workspace/.mcp.json" ]; then
    echo "MCP configuration already exists"
else
    echo "Creating MCP configuration..."
    cat > /workspace/.mcp.json << 'EOF'
{
  "mcpServers": {
    "claude-flow": {
      "command": "npx",
      "args": [
        "claude-flow@alpha",
        "mcp",
        "start"
      ],
      "type": "stdio"
    },
    "ruv-swarm": {
      "command": "npx",
      "args": [
        "ruv-swarm@latest",
        "mcp",
        "start"
      ],
      "type": "stdio"
    },
    "blender-tcp": {
      "command": "node",
      "args": [
        "/workspace/mcp-blender-client.js"
      ],
      "type": "stdio",
      "env": {
        "BLENDER_HOST": "${BLENDER_HOST:-192.168.0.216}",
        "BLENDER_PORT": "${BLENDER_PORT:-9876}"
      }
    },
    "kicad-mcp": {
      "command": "python3",
      "args": [
        "/app/mcp-tools/kicad_mcp.py"
      ],
      "type": "stdio"
    },
    "ngspice-mcp": {
      "command": "python3",
      "args": [
        "/app/mcp-tools/ngspice_mcp.py"
      ],
      "type": "stdio"
    },
    "imagemagick-mcp": {
      "command": "python3",
      "args": [
        "/app/mcp-tools/imagemagick_mcp.py"
      ],
      "type": "stdio"
    },
    "pbr-generator-mcp": {
      "command": "python3",
      "args": [
        "/app/mcp-tools/pbr_generator_mcp.py"
      ],
      "type": "stdio"
    }
  }
}
EOF
fi

# Step 3: Test MCP servers
echo -e "\n${YELLOW}Step 3: Testing MCP servers...${NC}"

# Test Claude Flow
test_mcp_server "Claude Flow" "npx claude-flow@alpha --version"

# Test Ruv Swarm
test_mcp_server "Ruv Swarm" "npx ruv-swarm@latest --version"

# Test Blender connection (if host is reachable)
if [ -n "${BLENDER_HOST}" ]; then
    echo -e "${YELLOW}Testing Blender MCP connection to ${BLENDER_HOST}:${BLENDER_PORT}...${NC}"
    if nc -z -w5 ${BLENDER_HOST} ${BLENDER_PORT} 2>/dev/null; then
        echo -e "${GREEN}✓ Blender MCP server is reachable${NC}"
    else
        echo -e "${YELLOW}! Blender MCP server not reachable (will retry when needed)${NC}"
    fi
fi

# Test local MCP tools
test_mcp_server "KiCad MCP" "python3 -c 'import sys; sys.path.append(\"/app/mcp-tools\"); import kicad_mcp; print(\"KiCad MCP ready\")'"
test_mcp_server "NGSpice MCP" "python3 -c 'import sys; sys.path.append(\"/app/mcp-tools\"); import ngspice_mcp; print(\"NGSpice MCP ready\")'"
test_mcp_server "ImageMagick MCP" "python3 -c 'import sys; sys.path.append(\"/app/mcp-tools\"); import imagemagick_mcp; print(\"ImageMagick MCP ready\")'"

# Step 4: Initialize Claude settings
echo -e "\n${YELLOW}Step 4: Initializing Claude settings...${NC}"

# Run the existing init script if available
if [ -f "/workspace/init-claude-settings.sh" ]; then
    bash /workspace/init-claude-settings.sh
fi

# Step 5: Create helper scripts
echo -e "\n${YELLOW}Step 5: Creating helper scripts...${NC}"

# Create MCP status script
cat > /workspace/mcp-status.sh << 'EOF'
#!/bin/bash
# Check status of all MCP servers

echo "MCP Server Status:"
echo "=================="

# Check Claude Flow
echo -n "Claude Flow: "
if npx claude-flow@alpha --version >/dev/null 2>&1; then
    echo "✓ Installed ($(npx claude-flow@alpha --version 2>/dev/null))"
else
    echo "✗ Not installed"
fi

# Check Ruv Swarm
echo -n "Ruv Swarm: "
if npx ruv-swarm@latest --version >/dev/null 2>&1; then
    echo "✓ Installed ($(npx ruv-swarm@latest --version 2>/dev/null))"
else
    echo "✗ Not installed"
fi

# Check Blender connection
echo -n "Blender MCP: "
if [ -n "${BLENDER_HOST}" ] && nc -z -w2 ${BLENDER_HOST} ${BLENDER_PORT} 2>/dev/null; then
    echo "✓ Reachable at ${BLENDER_HOST}:${BLENDER_PORT}"
else
    echo "✗ Not reachable at ${BLENDER_HOST:-not_set}:${BLENDER_PORT:-9876}"
fi

# Check local MCP tools
echo -n "KiCad MCP: "
if [ -f "/app/mcp-tools/kicad_mcp.py" ]; then
    echo "✓ Available"
else
    echo "✗ Not found"
fi

echo -n "NGSpice MCP: "
if [ -f "/app/mcp-tools/ngspice_mcp.py" ]; then
    echo "✓ Available"
else
    echo "✗ Not found"
fi

echo -n "ImageMagick MCP: "
if [ -f "/app/mcp-tools/imagemagick_mcp.py" ]; then
    echo "✓ Available"
else
    echo "✗ Not found"
fi

echo -n "OSS CAD Suite: "
if [ -d "/opt/oss-cad-suite" ]; then
    echo "✓ Installed at /opt/oss-cad-suite"
else
    echo "✗ Not found"
fi

# Check MCP configuration
echo -n "MCP Config: "
if [ -f "/workspace/.mcp.json" ]; then
    echo "✓ Found at /workspace/.mcp.json"
else
    echo "✗ Not found"
fi
EOF

chmod +x /workspace/mcp-status.sh

# Create Blender MCP test script
cat > /workspace/test-blender-mcp.sh << 'EOF'
#!/bin/bash
# Test Blender MCP connection

BLENDER_HOST=${BLENDER_HOST:-192.168.0.216}
BLENDER_PORT=${BLENDER_PORT:-9876}

echo "Testing Blender MCP connection..."
echo "Host: $BLENDER_HOST"
echo "Port: $BLENDER_PORT"

# Test TCP connection
if nc -z -w5 $BLENDER_HOST $BLENDER_PORT 2>/dev/null; then
    echo "✓ TCP connection successful"

    # Try to send a test message
    echo '{"jsonrpc":"2.0","method":"ping","id":1}' | nc -w2 $BLENDER_HOST $BLENDER_PORT
else
    echo "✗ Cannot connect to Blender MCP server"
    echo ""
    echo "Troubleshooting:"
    echo "1. Ensure Blender is running on $BLENDER_HOST"
    echo "2. Ensure Blender MCP addon is enabled and server is started"
    echo "3. Check firewall settings on the Blender host"
    echo "4. Try: BLENDER_HOST=<your-ip> ./test-blender-mcp.sh"
fi
EOF

chmod +x /workspace/test-blender-mcp.sh

echo -e "\n${GREEN}======================================"
echo -e "MCP Server Initialization Complete!"
echo -e "======================================${NC}"
echo ""
echo "Available commands:"
echo "  ./mcp-status.sh       - Check MCP server status"
echo "  ./test-blender-mcp.sh - Test Blender MCP connection"
echo ""
echo "To use MCP servers in Claude:"
echo "1. Ensure .mcp.json is in your workspace"
echo "2. MCP tools will be available with mcp__ prefix"
echo "3. For Blender: Set BLENDER_HOST and BLENDER_PORT if needed"