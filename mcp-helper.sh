#!/bin/bash
# MCP Helper Script - Ensures proper usage of claude-flow with local .mcp.json

set -e

# Configuration
MCP_CONFIG_FILE="./.mcp.json"
CLAUDE_FLOW_BIN="./node_modules/.bin/claude-flow"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
error() {
    echo -e "${RED}❌ Error: $1${NC}" >&2
    exit 1
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    if [[ ! -f "$MCP_CONFIG_FILE" ]]; then
        error "MCP configuration file not found: $MCP_CONFIG_FILE"
    fi
    
    if [[ ! -f "$CLAUDE_FLOW_BIN" ]]; then
        error "Claude Flow not installed. Run: npm install claude-flow@alpha"
    fi
}

# Show help
show_help() {
    cat << EOF
🔧 MCP Helper Script - Proper claude-flow usage with local configuration

USAGE:
    $0 <command> [arguments]

COMMANDS:
    list-tools                    List all available MCP tools
    list-servers                  List all MCP servers
    test-tool <tool-name>         Test if a tool is available
    run-tool <tool-name> <json>   Execute a tool with JSON input
    test-imagemagick             Run ImageMagick test (creates red square)
    test-all                     Run all available tests
    claude-instructions          Show instructions for Claude
    help                         Show this help message

EXAMPLES:
    $0 list-tools
    $0 test-tool imagemagick-mcp
    $0 run-tool imagemagick-mcp '{"method": "create", "params": {"width": 100, "height": 100, "color": "blue", "output": "test.png"}}'
    $0 test-imagemagick
    $0 claude-instructions

IMPORTANT:
    This script automatically uses --file $MCP_CONFIG_FILE to ensure 
    the correct tools are loaded from your local configuration.
EOF
}

# List all tools
list_tools() {
    info "Listing all MCP tools from $MCP_CONFIG_FILE"
    $CLAUDE_FLOW_BIN mcp tools --file "$MCP_CONFIG_FILE"
}

# List all servers  
list_servers() {
    info "Listing all MCP servers from $MCP_CONFIG_FILE"
    $CLAUDE_FLOW_BIN mcp servers --file "$MCP_CONFIG_FILE" 2>/dev/null || {
        warning "Server listing not available, showing tools instead:"
        list_tools
    }
}

# Test if a tool is available
test_tool() {
    local tool_name="$1"
    if [[ -z "$tool_name" ]]; then
        error "Tool name required. Usage: $0 test-tool <tool-name>"
    fi
    
    info "Testing if tool '$tool_name' is available..."
    if $CLAUDE_FLOW_BIN mcp tools --file "$MCP_CONFIG_FILE" | grep -q "$tool_name"; then
        success "Tool '$tool_name' is available"
        return 0
    else
        error "Tool '$tool_name' is NOT available"
        return 1
    fi
}

# Run a tool with JSON input
run_tool() {
    local tool_name="$1"
    local json_input="$2"
    
    if [[ -z "$tool_name" || -z "$json_input" ]]; then
        error "Usage: $0 run-tool <tool-name> '<json-input>'"
    fi
    
    info "Running tool '$tool_name' with input: $json_input"
    echo "$json_input" | $CLAUDE_FLOW_BIN mcp tool "$tool_name" --file "$MCP_CONFIG_FILE"
}

# Test ImageMagick functionality
test_imagemagick() {
    info "Testing ImageMagick MCP tool..."
    
    if ! test_tool "imagemagick-mcp" >/dev/null 2>&1; then
        error "ImageMagick MCP tool not available"
    fi
    
    local test_file="mcp-test-red-square.png"
    local json_input='{"method": "create", "params": {"width": 100, "height": 100, "color": "red", "output": "'$test_file'"}}'
    
    info "Creating red square: $test_file"
    run_tool "imagemagick-mcp" "$json_input"
    
    if [[ -f "$test_file" ]]; then
        success "ImageMagick test passed! Created: $test_file"
        ls -la "$test_file"
    else
        error "ImageMagick test failed - file not created"
    fi
}

# Run all tests
test_all() {
    info "Running all available tests..."
    
    echo "=== Test 1: Tool Availability ==="
    test_tool "imagemagick-mcp" || true
    test_tool "blender-mcp" || true
    test_tool "qgis-mcp" || true
    
    echo -e "\n=== Test 2: ImageMagick Functionality ==="
    test_imagemagick || true
    
    echo -e "\n=== Test 3: All Available Tools ==="
    list_tools
}

# Show Claude instructions
claude_instructions() {
    cat << EOF
📋 INSTRUCTIONS FOR CLAUDE

Copy and paste this instruction to Claude at the start of your session:

┌─────────────────────────────────────────────────────────────────┐
│ IMPORTANT: For this session, whenever you need to interact with │
│ MCP tools using claude-flow, you MUST use the --file flag:      │
│                                                                 │
│ To list tools:                                                  │
│   ./node_modules/.bin/claude-flow mcp tools --file ./.mcp.json │
│                                                                 │
│ To use a tool:                                                  │
│   echo '<json>' | ./node_modules/.bin/claude-flow mcp tool \\   │
│     <tool-name> --file ./.mcp.json                             │
│                                                                 │
│ Available helper script: ./mcp-helper.sh                       │
└─────────────────────────────────────────────────────────────────┘

QUICK TEST FOR CLAUDE:
Ask Claude to run: ./mcp-helper.sh list-tools

EXAMPLE TASK FOR CLAUDE:  
"Using the imagemagick-mcp tool, create a 150x150 blue square and save it as blue_square.png"

The helper script ./mcp-helper.sh provides convenient wrappers for common operations.
EOF
}

# Main script logic
main() {
    check_prerequisites
    
    case "${1:-help}" in
        "list-tools"|"tools")
            list_tools
            ;;
        "list-servers"|"servers")
            list_servers
            ;;
        "test-tool")
            test_tool "$2"
            ;;
        "run-tool")
            run_tool "$2" "$3"
            ;;
        "test-imagemagick")
            test_imagemagick
            ;;
        "test-all")
            test_all
            ;;
        "claude-instructions"|"instructions")
            claude_instructions
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            error "Unknown command: $1. Use '$0 help' for usage information."
            ;;
    esac
}

# Run main function
main "$@"