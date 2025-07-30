#!/bin/bash
# Test script for MCP connectivity between containers

echo "MCP Connectivity Test Script"
echo "============================"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
BLENDER_HOST="${BLENDER_HOST:-blender_desktop}"
BLENDER_PORT="${BLENDER_PORT:-9876}"
QGIS_HOST="${QGIS_HOST:-blender_desktop}"
QGIS_PORT="${QGIS_PORT:-9877}"

echo "Current configuration:"
echo "  BLENDER_HOST: $BLENDER_HOST"
echo "  BLENDER_PORT: $BLENDER_PORT"
echo "  QGIS_HOST: $QGIS_HOST"
echo "  QGIS_PORT: $QGIS_PORT"
echo

# Function to test network connectivity
test_network() {
    local host=$1
    local port=$2
    local service=$3
    
    echo -n "Testing $service at $host:$port... "
    
    if timeout 5 bash -c "</dev/tcp/$host/$port" 2>/dev/null; then
        echo -e "${GREEN}✓ Connected${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed${NC}"
        return 1
    fi
}

# Function to test MCP communication
test_mcp_communication() {
    local host=$1
    local port=$2
    local service=$3
    
    echo -n "Testing MCP protocol for $service... "
    
    # Create a simple test request
    local test_request='{"type":"ping","params":{}}'
    
    # Try to send request and get response
    if response=$(echo "$test_request" | timeout 5 nc -w 2 "$host" "$port" 2>/dev/null); then
        if [ -n "$response" ]; then
            echo -e "${GREEN}✓ Response received${NC}"
            echo "  Response: $response"
            return 0
        else
            echo -e "${YELLOW}⚠ Connected but no response${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ Communication failed${NC}"
        return 1
    fi
}

# Check network connectivity
echo "1. Network Connectivity Tests"
echo "-----------------------------"
test_network "$BLENDER_HOST" "$BLENDER_PORT" "Blender MCP"
blender_network=$?

test_network "$QGIS_HOST" "$QGIS_PORT" "QGIS MCP"
qgis_network=$?

echo

# Check Docker network
echo "2. Docker Network Check"
echo "----------------------"
echo -n "Current container network(s): "
if [ -f /.dockerenv ]; then
    # We're in a container
    networks=$(ip addr | grep -E "inet .* scope global" | awk '{print $2}' | cut -d'/' -f1)
    echo "$networks"
    
    echo -n "Checking if on docker_ragflow network... "
    if docker network inspect docker_ragflow 2>/dev/null | grep -q "$(hostname)"; then
        echo -e "${GREEN}✓ Yes${NC}"
    else
        echo -e "${RED}✗ No${NC}"
        echo -e "${YELLOW}Run: docker network connect docker_ragflow $(hostname)${NC}"
    fi
else
    echo -e "${YELLOW}Not running in Docker container${NC}"
fi

echo

# Check MCP bridge scripts
echo "3. MCP Bridge Scripts Check"
echo "--------------------------"
echo -n "Blender MCP bridge script... "
if [ -f /workspace/scripts/mcp-blender-client.js ]; then
    echo -e "${GREEN}✓ Found${NC}"
else
    echo -e "${RED}✗ Not found${NC}"
fi

echo -n "QGIS MCP bridge script... "
if [ -f /workspace/mcp-tools/qgis_mcp.py ]; then
    echo -e "${GREEN}✓ Found${NC}"
else
    echo -e "${RED}✗ Not found${NC}"
fi

echo

# Test MCP communication if network is available
if [ $blender_network -eq 0 ] || [ $qgis_network -eq 0 ]; then
    echo "4. MCP Protocol Tests"
    echo "--------------------"
    
    if [ $blender_network -eq 0 ]; then
        test_mcp_communication "$BLENDER_HOST" "$BLENDER_PORT" "Blender"
    fi
    
    if [ $qgis_network -eq 0 ]; then
        test_mcp_communication "$QGIS_HOST" "$QGIS_PORT" "QGIS"
    fi
else
    echo -e "${YELLOW}Skipping MCP protocol tests due to network connectivity issues${NC}"
fi

echo
echo "5. Recommendations"
echo "-----------------"

if [ $blender_network -ne 0 ] || [ $qgis_network -ne 0 ]; then
    echo -e "${RED}Network connectivity issues detected!${NC}"
    echo
    echo "To fix:"
    echo "1. Ensure the Blender container is running:"
    echo "   cd /workspace/blender-docker && docker-compose up -d"
    echo
    echo "2. Connect this container to the docker_ragflow network:"
    echo "   docker network connect docker_ragflow $(hostname)"
    echo
    echo "3. Set environment variables and restart Claude:"
    echo "   source /workspace/blender-docker/setup-mcp-env.sh"
else
    echo -e "${GREEN}Network connectivity looks good!${NC}"
    echo
    echo "Next steps:"
    echo "1. Ensure environment variables are set:"
    echo "   source /workspace/blender-docker/setup-mcp-env.sh"
    echo
    echo "2. Restart Claude MCP to pick up the configuration"
    echo
    echo "3. Check MCP server list:"
    echo "   claude mcp list"
fi