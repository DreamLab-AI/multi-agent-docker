# Quick Start Guide

Get up and running with the Multi-Agent Docker Environment in under 5 minutes!

## 🚀 TL;DR

```bash
# 1. Clone & enter directory
git clone <repository-url> && cd multi-agent-docker

# 2. Build & start using the helper script
./multi-agent.sh build
./multi-agent.sh start

# 3. Initialize workspace (automatic shell entry)
/app/setup-workspace.sh

# 4. Verify everything works
./mcp-helper.sh list-tools
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

```bash
# Build the image
./multi-agent.sh build

# Start the container (automatically enters shell)
./multi-agent.sh start
```

Expected output:
```
Container started! Waiting for health checks...
Multi-Agent Container Status:
=============================
NAME                    IMAGE                       STATUS                   PORTS
multi-agent-container   multi-agent-docker:latest   Up X seconds (healthy)   3000->3000/tcp, 3002->3002/tcp...

Entering multi-agent container as 'dev' user...
dev@xxxxxxxxxxxx:/workspace$
```

### Step 3: Initialize Your Workspace

```bash
/app/setup-workspace.sh
```

This will:
- ✅ Copy MCP tools and helper scripts to workspace
- ✅ Set proper executable permissions
- ✅ Install Claude Flow locally
- ✅ Update CLAUDE.md with tool knowledge
- ✅ Verify all tools are working

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

You know everything is working when:

1. `./mcp-helper.sh list-tools` shows all 6 tools:
   ```
   ✅ imagemagick-mcp - Image manipulation and creation
   ✅ blender-mcp - 3D modeling and rendering
   ✅ qgis-mcp - Geospatial analysis
   ✅ kicad-mcp - Electronic design automation
   ✅ ngspice-mcp - Circuit simulation
   ✅ pbr-generator-mcp - PBR texture generation
   ```

2. `./mcp-helper.sh test-all` passes all tests

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
./mcp-helper.sh run-tool pbr-generator-mcp '{"material": "brushed_metal", "resolution": "1024x1024", "output_dir": "./pbr_textures"}'
```

### Test 3D Tools

```bash
# Connect to external Blender (if running on port 9876)
./mcp-helper.sh run-tool blender-mcp '{"action": "status"}'

# Test QGIS capabilities
./mcp-helper.sh run-tool qgis-mcp '{"action": "info"}'
```

## ⚡ Quick Commands Reference

| Command | Description |
|---------|-------------|
| `./multi-agent.sh start` | Start container (auto-enters shell) |
| `./multi-agent.sh shell` | Enter running container |
| `./multi-agent.sh logs` | View container logs |
| `./multi-agent.sh stop` | Stop container |
| `./mcp-helper.sh list-tools` | List all MCP tools |
| `./mcp-helper.sh test-all` | Test all tools |
| `./mcp-helper.sh claude-instructions` | Get Claude usage guide |
| `exit` | Leave container |

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