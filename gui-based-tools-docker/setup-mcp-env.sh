#!/bin/bash
# Setup script for MCP environment variables in Claude agent container

# This script should be sourced in the Claude agent container to set up
# proper environment variables for cross-container MCP communication

echo "Setting up MCP environment variables for cross-container communication..."

# Check if we're running in a container
if [ -f /.dockerenv ]; then
    echo "Running in Docker container"
else
    echo "Warning: Not running in a Docker container"
fi

# Export environment variables for MCP bridge scripts
export BLENDER_HOST="${BLENDER_HOST:-blender_desktop}"
export BLENDER_PORT="${BLENDER_PORT:-9876}"
export QGIS_HOST="${QGIS_HOST:-blender_desktop}"
export QGIS_PORT="${QGIS_PORT:-9877}"

echo "MCP Environment configured:"
echo "  BLENDER_HOST: $BLENDER_HOST"
echo "  BLENDER_PORT: $BLENDER_PORT"
echo "  QGIS_HOST: $QGIS_HOST"
echo "  QGIS_PORT: $QGIS_PORT"

# Test connectivity function
test_connectivity() {
    echo ""
    echo "Testing connectivity to MCP services..."
    
    # Test Blender MCP
    if nc -zv "$BLENDER_HOST" "$BLENDER_PORT" 2>&1 | grep -q "succeeded"; then
        echo "✓ Blender MCP connection successful ($BLENDER_HOST:$BLENDER_PORT)"
    else
        echo "✗ Blender MCP connection failed ($BLENDER_HOST:$BLENDER_PORT)"
        echo "  Make sure the Blender container is running and on the same network"
    fi
    
    # Test QGIS MCP
    if nc -zv "$QGIS_HOST" "$QGIS_PORT" 2>&1 | grep -q "succeeded"; then
        echo "✓ QGIS MCP connection successful ($QGIS_HOST:$QGIS_PORT)"
    else
        echo "✗ QGIS MCP connection failed ($QGIS_HOST:$QGIS_PORT)"
        echo "  Make sure QGIS MCP is running and on the same network"
    fi
}

# Add function to path for easy testing
alias test-mcp-connectivity=test_connectivity

echo ""
echo "To test connectivity, run: test-mcp-connectivity"
echo ""
echo "Next steps:"
echo "1. Ensure your container is connected to the docker_ragflow network:"
echo "   docker network connect docker_ragflow \$(hostname)"
echo "2. Test connectivity with: test-mcp-connectivity"
echo "3. Restart Claude MCP to pick up the new environment variables"