# MCP Server Integration Guide

## Overview

I've successfully prepared three MCP servers for integration with Claude Code:

1. **Blender MCP** - 3D modeling and scene manipulation
2. **Revit MCP** - Autodesk Revit integration
3. **Unreal MCP** - Unreal Engine 5.5+ control

## Current Status

### ✅ Completed
- Analyzed all three MCP server repositories
- Copied repositories to workspace for access
- Built Revit MCP server successfully
- Created test scripts for connection validation
- Prepared configuration files

### ⚠️ Pending
- Blender is not currently running on the host system
- MCP servers need to be added to Claude Code configuration
- Connection testing requires host applications to be running

## Integration Instructions

### Option 1: Using Claude CLI (Recommended)

```bash
# Add Blender MCP server
claude mcp add blender uvx blender-mcp

# Add Revit MCP server (after building)
claude mcp add revit node /workspace/revit-mcp/build/index.js

# Add Unreal MCP server
claude mcp add unreal uv --directory /workspace/unreal-mcp-source/Python run unreal_mcp_server.py
```

### Option 2: Manual Configuration

Add the following to your `~/.claude/settings.json` file:

```json
{
  "mcpServers": {
    "blender": {
      "command": "uvx",
      "args": ["blender-mcp"],
      "env": {
        "BLENDER_HOST": "host.docker.internal",
        "BLENDER_PORT": "9876"
      }
    },
    "revit": {
      "command": "node",
      "args": ["/workspace/revit-mcp/build/index.js"]
    },
    "unreal": {
      "command": "uv",
      "args": [
        "--directory",
        "/workspace/unreal-mcp-source/Python",
        "run",
        "unreal_mcp_server.py"
      ]
    }
  }
}
```

## Server-Specific Setup

### Blender MCP Setup

1. **Install Blender Addon on Host**:
   - Copy `/workspace/blender-mcp-source/addon.py` to your host system
   - Open Blender (3.0 or newer)
   - Go to Edit > Preferences > Add-ons
   - Click "Install..." and select the addon.py file
   - Enable "Interface: Blender MCP" addon

2. **Start Blender Server**:
   - In Blender's 3D View, press N to open sidebar
   - Find the "BlenderMCP" tab
   - Click "Connect to Claude"
   - Server will listen on port 9876

3. **Test Connection**:
   ```bash
   python /workspace/test-blender-connection.py
   ```

### Revit MCP Setup

1. **Prerequisites**:
   - Install [revit-mcp-plugin](https://github.com/revit-mcp/revit-mcp-plugin) in Revit
   - Ensure Node.js 18+ is installed

2. **Server is Ready**:
   - Already built at `/workspace/revit-mcp/build/index.js`
   - Connects via socket to Revit plugin

### Unreal MCP Setup

1. **Prerequisites**:
   - Unreal Engine 5.5+
   - Python 3.12+
   - Copy UnrealMCP plugin to your Unreal project

2. **Enable Plugin**:
   - In Unreal: Edit > Plugins
   - Find "UnrealMCP" and enable
   - Restart editor
   - Server listens on port 55557

## Connection Architecture

```
Claude Code (Container)
    ├── Blender MCP → TCP 9876 → Blender (Host)
    ├── Revit MCP → Socket → Revit Plugin (Host)
    └── Unreal MCP → TCP 55557 → Unreal Engine (Host)
```

## Docker Networking

From within the Docker container, host applications are accessible via:
- `host.docker.internal` (Docker Desktop on Mac/Windows)
- `172.17.0.1` (Default Docker bridge on Linux)

## Available Tools

### Blender MCP Tools
- get_scene_info - Get current scene information
- create_object - Create 3D objects
- delete_object - Delete objects by name
- set_object_transform - Modify position/rotation/scale
- apply_material - Apply materials to objects
- execute_blender_code - Run arbitrary Python code

### Revit MCP Tools
- get_current_view_info - Get view information
- get_current_view_elements - List elements in view
- create_point_based_element - Create doors, windows, furniture
- create_line_based_element - Create walls, beams, pipes
- modify_element - Change element properties
- send_code_to_revit - Execute Revit API code

### Unreal MCP Tools
- Actor management (create, delete, transform)
- Blueprint creation and compilation
- Node graph manipulation
- Editor viewport control
- Component configuration
- Input mapping setup

## Troubleshooting

### Connection Issues
1. Ensure host applications are running
2. Check firewall settings for ports 9876 (Blender) and 55557 (Unreal)
3. Verify addon/plugin installation
4. Use test scripts to validate connections

### Common Errors
- "Connection refused" - Application not running or server not started
- "Permission denied" - Check file permissions and user access
- "Module not found" - Install required dependencies

## Next Steps

1. Install the respective addons/plugins on your host applications
2. Start the applications and enable their MCP servers
3. Add the MCP servers to Claude Code configuration
4. Test connections using the provided scripts
5. Begin using natural language to control your 3D applications!