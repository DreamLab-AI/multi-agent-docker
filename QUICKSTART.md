# Quick Start Guide

Get up and running with the Multi-Agent Docker Environment in under 5 minutes!

## 🚀 TL;DR

```bash
# 1. Clone & enter directory
git clone <repository-url> && cd multi-agent-docker

# 2. Build and start the environment
./multi-agent.sh build
./multi-agent.sh start

# 3. Inside the container shell, initialize the workspace
/app/setup-workspace.sh

# 4. Verify the setup
./mcp-helper.sh test-all
```

## 📋 Prerequisites Checklist

- [ ] Docker Engine installed
- [ ] Docker Compose installed
- [ ] Git installed
- [ ] 8GB+ RAM available
- [ ] 20GB+ disk space

## 🎯 Step-by-Step Guide

### Step 1: Get the Code

```bash
git clone <repository-url>
cd multi-agent-docker
```

### Step 2: Build and Start

The `multi-agent.sh` script simplifies the setup process.

First, build the Docker images:
```bash
./multi-agent.sh build
```

Then, start the services. This command will start the containers in the background and automatically open a shell into the `multi-agent-container`:
```bash
./multi-agent.sh start
```

You will see output indicating the containers are starting, followed by the container's command prompt:
```
Starting multi-agent container...
...
Container started! Waiting for health checks...
...
Multi-Agent Container Status:
=============================
NAME                      IMAGE                             STATUS              PORTS
gui-tools-container       multi-agent-docker_gui-tools      Up About a minute   0.0.0.0:5901->5901/tcp, 0.0.0.0:9876-9878->9876-9878/tcp
multi-agent-container     multi-agent-docker_multi-agent    Up About a minute   0.0.0.0:3000->3000/tcp, 0.0.0.0:3002->3002/tcp

Entering multi-agent container as 'dev' user...
dev@multi-agent-container:/workspace$
```

### Step 3: Initialize Your Workspace

Once inside the container, run the setup script. This only needs to be done the first time you start the environment.
```bash
/app/setup-workspace.sh
```
This script prepares your environment by:
- ✅ Copying the latest MCP tools and helper scripts into your workspace.
- ✅ Setting the correct executable permissions.
- ✅ Installing the `claude-flow` orchestrator via `npm`.
- ✅ Verifying that all configured MCP tools are responsive.

### Step 4: Test MCP Tools

```bash
# List all available tools
./mcp-helper.sh list-tools

# Test all tools automatically
./mcp-helper.sh test-all

# Test a specific tool (ImageMagick example)
./mcp-helper.sh test-imagemagick
```

## 🎉 Success Indicators

You'll know the environment is fully operational when you can confirm the following:

1.  **Both Containers are Running**: Open a new terminal on your host machine and run `./multi-agent.sh status`. You should see both `multi-agent-container` and `gui-tools-container` with a `Up` status.

2.  **VNC Access to GUI Tools**:
    *   Open your favorite VNC client (e.g., RealVNC, TigerVNC).
    *   Connect to `localhost:5901`.
    *   You should see the XFCE desktop environment of the `gui-tools-container`, with applications like Blender and QGIS running.

3.  **All MCP Tools Pass Tests**:
    *   Inside the `multi-agent-container` shell, run the test script:
        ```bash
        ./mcp-helper.sh test-all
        ```
    *   All tests should pass, indicating that the bridges to the external GUI applications are working correctly.

## 🔥 Common First Tasks

### Test ImageMagick Tool

```bash
# Quick test using helper
./mcp-helper.sh test-imagemagick

# Manual test - create a golden square
./mcp-helper.sh run-tool imagemagick-mcp '{"method": "create", "params": {"width": 200, "height": 200, "color": "gold", "output": "gold_square.png"}}'
```

### Test PBR Generator

```bash
# Generate a metal PBR texture set
./mcp-helper.sh run-tool pbr-generator-mcp '{"tool": "generate_material", "params": {"material": "brushed_metal", "resolution": "1024x1024", "output": "./pbr_textures"}}'
```

### Test 3D Tools

The 3D tools run in the `gui-tools-container` and are accessed via a bridge.

```bash
# Create a simple cube in Blender
./mcp-helper.sh run-tool blender-mcp '{"tool": "execute_code", "params": {"code": "import bpy; bpy.ops.mesh.primitive_cube_add()"}}'

# Check the QGIS version
./mcp-helper.sh run-tool qgis-mcp '{"tool": "get_qgis_version"}'
```
You can verify the cube was created by checking the VNC session at `localhost:5901`.

## ⚡ Quick Commands Reference

These commands are run from your **host machine's terminal**.

| Command | Description |
|---|---|
| `./multi-agent.sh build` | Builds or rebuilds the Docker images. |
| `./multi-agent.sh start` | Starts both containers and enters the `multi-agent-container` shell. |
| `./multi-agent.sh stop` | Stops and removes the containers. |
| `./multi-agent.sh restart` | Restarts the containers. |
| `./multi-agent.sh status` | Shows the status of the running containers. |
| `./multi-agent.sh logs` | Tails the logs from both containers. Use `logs -f` to follow. |
| `./multi-agent.sh shell` | Enters the shell of an already running `multi-agent-container`. |
| `./multi-agent.sh cleanup` | Stops containers and removes all associated volumes (deletes all data). |

## 🆘 Quick Fixes

### "Tool not available" error
```bash
# Re-run setup with force flag
/app/setup-workspace.sh --force
```

### "Permission denied" error
```bash
# Fix ownership (should be automatic now)
sudo chown -R dev:dev /workspace
```

### "Helper script not found"
```bash
# Copy helper script manually
cp /app/mcp-helper.sh ./
chmod +x ./mcp-helper.sh
```

## 🎯 Working with Claude

The setup automatically provides Claude with MCP tool knowledge. To use tools with Claude:

```bash
# Get instructions for Claude
./mcp-helper.sh claude-instructions

# Example task for Claude:
# "Using the imagemagick-mcp tool, create a 300x300 blue gradient image"
# "Using the pbr-generator-mcp tool, create realistic wood textures"
```

## 📚 Next Steps

- Read the [Architecture Documentation](./ARCHITECTURE.md)
- Explore the [Agent Briefing](./AGENT-BRIEFING.md) for Claude
- Check out available [MCP Tools](#available-mcp-tools)
- Start building with the multi-agent environment!

## 🛠️ Available MCP Tools

| Tool | Purpose | Example Use |
|------|---------|-------------|
| **imagemagick-mcp** | Image creation & manipulation | Create graphics, resize, apply effects |
| **blender-mcp** | 3D modeling & rendering | Create 3D models, render scenes |
| **qgis-mcp** | Geospatial analysis | Process maps, analyze geographic data |
| **kicad-mcp** | Electronic design | Design PCBs, create schematics |
| **ngspice-mcp** | Circuit simulation | Simulate electronic circuits |
| **pbr-generator-mcp** | PBR texture creation | Generate realistic material textures |

---

**Need help?** Use `./mcp-helper.sh claude-instructions` or check the [Architecture Guide](./ARCHITECTURE.md)!