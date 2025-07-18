# Blender MCP Server Setup Guide

## Overview
The Blender MCP server enables Claude Code to control Blender 3D through a TCP connection. This guide covers the specific setup required for connecting Claude Code (on host) to Blender running inside a Docker container.

## Architecture

```
┌─────────────────────┐         ┌──────────────────────────┐
│   Host Machine      │         │    Docker Container      │
│                     │         │                          │
│  ┌──────────────┐   │  TCP    │  ┌───────────────────┐  │
│  │ Claude Code  │───┼─────────┼─►│ Blender MCP Server│  │
│  └──────────────┘   │  :9876   │  └───────────────────┘  │
│                     │         │           ▲              │
│                     │         │           │              │
│                     │         │  ┌────────┴──────────┐  │
│                     │         │  │ Blender Headless  │  │
│                     │         │  │   (Xvfb :99)      │  │
│                     │         │  └───────────────────┘  │
└─────────────────────┘         └──────────────────────────┘
```

## Prerequisites

1. Docker container running with Blender MCP
2. Port 9876 exposed from container to host
3. Claude Code installed on host machine

## Setup Methods

### Method 1: Using UVX (Recommended)

If you have `uvx` installed:

```bash
claude mcp add blender uvx blender-mcp
```

### Method 2: Direct TCP Configuration

```bash
claude mcp add-json blender '{
  "transport": "tcp",
  "host": "localhost",
  "port": 9876
}'
```

### Method 3: Manual Configuration

Add to `.claude/settings.json`:

```json
{
  "mcpServers": {
    "blender": {
      "transport": "tcp",
      "host": "localhost",
      "port": 9876
    }
  }
}
```

## Verification

### 1. Check Container Status
```bash
# Verify container is running
docker ps | grep blender

# Check port mapping
docker port <container-name> 9876
# Should show: 9876/tcp -> 0.0.0.0:9876
```

### 2. Test TCP Connection
```bash
# Test if port is open
telnet localhost 9876
# or
nc -zv localhost 9876
```

### 3. Check Blender Process
```bash
# Inside container
docker exec <container> ps aux | grep blender
```

### 4. Test MCP Connection
In Claude Code, run:
```
mcp__blender__get_scene_info
```

## Available MCP Tools

### Scene Management
- `mcp__blender__get_scene_info` - Get current scene information
- `mcp__blender__list_objects` - List all objects in scene
- `mcp__blender__select_object` - Select specific object
- `mcp__blender__delete_object` - Delete selected object

### Object Creation
- `mcp__blender__add_primitive` - Add primitive shapes (cube, sphere, etc.)
- `mcp__blender__add_mesh` - Add custom mesh
- `mcp__blender__add_light` - Add lighting
- `mcp__blender__add_camera` - Add camera

### Transformation
- `mcp__blender__transform_object` - Move, rotate, scale objects
- `mcp__blender__set_location` - Set precise location
- `mcp__blender__set_rotation` - Set precise rotation
- `mcp__blender__set_scale` - Set precise scale

### Materials & Textures
- `mcp__blender__create_material` - Create new material
- `mcp__blender__assign_material` - Assign material to object
- `mcp__blender__set_material_property` - Modify material properties

### Rendering
- `mcp__blender__render_image` - Render current view
- `mcp__blender__render_animation` - Render animation sequence
- `mcp__blender__get_viewport_screenshot` - Quick viewport capture
- `mcp__blender__set_render_settings` - Configure render settings

### File Operations
- `mcp__blender__save_file` - Save Blender file
- `mcp__blender__load_file` - Load Blender file
- `mcp__blender__export_mesh` - Export to various formats
- `mcp__blender__import_mesh` - Import from various formats

### Custom Python
- `mcp__blender__execute_blender_code` - Execute arbitrary Python code

## Example Workflows

### 1. Create a Simple Scene
```python
# Create a cube
mcp__blender__add_primitive(type="cube", location=[0, 0, 0])

# Add a light
mcp__blender__add_light(type="point", location=[5, 5, 5])

# Add a camera
mcp__blender__add_camera(location=[7, -7, 5])

# Render the scene
mcp__blender__render_image(output_path="/workspace/render.png")
```

### 2. Import and Modify Model
```python
# Import a model
mcp__blender__import_mesh(filepath="/workspace/model.obj")

# Scale it
mcp__blender__transform_object(name="imported_model", scale=[2, 2, 2])

# Add material
mcp__blender__create_material(name="gold")
mcp__blender__assign_material(object="imported_model", material="gold")
```

### 3. Execute Custom Script
```python
code = """
import bpy
# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create spiral
for i in range(50):
    bpy.ops.mesh.primitive_cube_add(
        location=(i*0.5, 0, i*0.2),
        rotation=(0, 0, i*0.1)
    )
"""
mcp__blender__execute_blender_code(code=code)
```

## Troubleshooting

### Connection Refused
1. Check if container is running: `docker ps`
2. Verify port mapping: `docker port <container> 9876`
3. Check Blender MCP logs: `docker logs <container> | grep mcp`

### MCP Tools Not Available
1. List configured servers: `claude mcp list`
2. Check server details: `claude mcp get blender`
3. Re-add server: `claude mcp remove blender && claude mcp add blender uvx blender-mcp`

### Blender Crashes
1. Check container logs: `docker logs <container>`
2. Verify Xvfb is running: `docker exec <container> ps aux | grep Xvfb`
3. Restart container: `docker restart <container>`

### Performance Issues
1. Allocate more resources to Docker
2. Use simpler scenes for testing
3. Enable GPU acceleration if available

## Docker Configuration

### Container Requirements
- Blender 4.5 LTS installed
- Xvfb for headless rendering
- Python with bpy module
- MCP server addon installed

### Environment Variables
```bash
DISPLAY=:99          # Virtual display
BLENDER_VERSION=4.5  # Blender version
BLENDER_PATH=/usr/local/blender
```

### Exposed Ports
- 9876: Blender MCP server

## Security Considerations

1. **Local Only**: Server only accepts localhost connections
2. **Sandboxed**: Runs in Docker container
3. **Limited Access**: Only Blender operations allowed
4. **No Shell Access**: Cannot execute system commands

## Advanced Configuration

### Custom Port
```json
{
  "mcpServers": {
    "blender": {
      "transport": "tcp",
      "host": "localhost",
      "port": 9877  // Custom port
    }
  }
}
```

### Remote Connection
```json
{
  "mcpServers": {
    "blender": {
      "transport": "tcp",
      "host": "remote-server.com",
      "port": 9876,
      "auth": {
        "type": "token",
        "token": "your-auth-token"
      }
    }
  }
}
```

## Integration with Claude Flow

Combine Blender MCP with Claude Flow for complex workflows:

```bash
# Initialize swarm for 3D project
mcp__claude-flow__swarm_init topology="hierarchical" maxAgents=5

# Spawn specialized agents
mcp__claude-flow__agent_spawn type="architect" name="3D Designer"
mcp__claude-flow__agent_spawn type="coder" name="Script Writer"

# Orchestrate 3D workflow
mcp__claude-flow__task_orchestrate task="Create animated 3D logo"
```

## Resources

- [Blender Python API](https://docs.blender.org/api/current/)
- [MCP Protocol Docs](https://modelcontextprotocol.io)
- [Docker Networking](https://docs.docker.com/network/)
- Container logs: `/var/log/blender-mcp.log`