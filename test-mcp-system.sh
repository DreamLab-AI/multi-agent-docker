#!/bin/bash
# Test script for MCP system integration

set -e

echo "========================================"
echo "MCP System Integration Test"
echo "========================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# Function to test a command
test_command() {
    local description=$1
    local command=$2
    
    echo -ne "${YELLOW}Testing: ${description}...${NC} "
    
    if eval "$command" >/dev/null 2>&1; then
        echo -e "${GREEN}PASSED${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}FAILED${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to test MCP tool
test_mcp_tool() {
    local server=$1
    local tool=$2
    local description=$3
    
    echo -ne "${YELLOW}Testing MCP: ${description}...${NC} "
    
    # This would need to be run inside Claude Code with MCP access
    # For now, we'll just check if the server responds
    if npx $server --version >/dev/null 2>&1; then
        echo -e "${GREEN}AVAILABLE${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}NOT AVAILABLE${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo -e "\n${YELLOW}1. Testing Basic Environment${NC}"
echo "================================"

test_command "Node.js installation" "node --version"
test_command "NPM installation" "npm --version"
test_command "Docker access" "docker --version"
test_command "Workspace directory" "[ -d /workspace ]"
test_command "MCP config exists" "[ -f /workspace/.mcp.json ]"

echo -e "\n${YELLOW}2. Testing MCP Servers${NC}"
echo "======================="

test_command "Claude Flow installed" "npx claude-flow@alpha --version"
test_command "Ruv Swarm installed" "npx ruv-swarm@latest --version"
test_command "Blender client script" "[ -f /workspace/mcp-blender-client.js ]"

echo -e "\n${YELLOW}3. Testing Network Connectivity${NC}"
echo "================================"

# Test localhost
test_command "Localhost connectivity" "ping -c 1 localhost"

# Test Blender host (may fail if not on same network)
BLENDER_HOST=${BLENDER_HOST:-192.168.0.216}
BLENDER_PORT=${BLENDER_PORT:-9876}

echo -ne "${YELLOW}Testing: Blender host reachability...${NC} "
if nc -z -w2 $BLENDER_HOST $BLENDER_PORT 2>/dev/null; then
    echo -e "${GREEN}REACHABLE${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}NOT REACHABLE (expected if not on same network)${NC}"
fi

echo -e "\n${YELLOW}4. Testing Helper Scripts${NC}"
echo "=========================="

test_command "MCP status script" "[ -x /workspace/mcp-status.sh ]"
test_command "Blender test script" "[ -x /workspace/test-blender-mcp.sh ]"
test_command "Init script" "[ -x /workspace/init-mcp-servers.sh ]"

echo -e "\n${YELLOW}5. Testing MCP Configuration${NC}"
echo "============================="

# Check MCP JSON structure
echo -ne "${YELLOW}Testing: MCP JSON validity...${NC} "
if jq . /workspace/.mcp.json >/dev/null 2>&1; then
    echo -e "${GREEN}VALID${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}INVALID${NC}"
    ((TESTS_FAILED++))
fi

# Check for required MCP servers in config
echo -ne "${YELLOW}Testing: Claude Flow in config...${NC} "
if jq -e '.mcpServers["claude-flow"]' /workspace/.mcp.json >/dev/null 2>&1; then
    echo -e "${GREEN}FOUND${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}NOT FOUND${NC}"
    ((TESTS_FAILED++))
fi

echo -ne "${YELLOW}Testing: Ruv Swarm in config...${NC} "
if jq -e '.mcpServers["ruv-swarm"]' /workspace/.mcp.json >/dev/null 2>&1; then
    echo -e "${GREEN}FOUND${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}NOT FOUND${NC}"
    ((TESTS_FAILED++))
fi

echo -ne "${YELLOW}Testing: Blender TCP in config...${NC} "
if jq -e '.mcpServers["blender-tcp"]' /workspace/.mcp.json >/dev/null 2>&1; then
    echo -e "${GREEN}FOUND${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}NOT FOUND${NC}"
    ((TESTS_FAILED++))
fi

echo -e "\n${YELLOW}6. Testing Claude Settings${NC}"
echo "==========================="

test_command "Claude settings directory" "[ -d /workspace/.claude ]"
test_command "Claude settings file" "[ -f /workspace/.claude/settings.json ]"

# Summary
echo -e "\n========================================"
echo -e "${YELLOW}Test Summary${NC}"
echo "========================================"
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed! MCP system is ready.${NC}"
    exit 0
else
    echo -e "\n${RED}✗ Some tests failed. Please check the configuration.${NC}"
    exit 1
fi