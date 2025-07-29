# Quick Start Guide

Get up and running with the Multi-Agent Docker Environment in under 5 minutes!

## 🚀 TL;DR

```bash
# 1. Clone & enter directory
git clone <repository-url> && cd multi-agent-docker

# 2. Build & start
docker-compose up -d --build

# 3. Enter container
docker exec -it multi-agent-container /bin/zsh

# 4. Initialize workspace (inside container)
/app/setup-workspace.sh

# 5. Verify everything works
mcp-status
claude-flow mcp tools
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
# Build the image and start the container
docker-compose up -d --build

# Check if container is running
docker ps | grep multi-agent-container
```

Expected output:
```
CONTAINER ID   IMAGE                    STATUS         PORTS                    NAMES
xxxxxxxxxxxx   multi-agent-docker:latest   Up X minutes   3000/tcp, 3002/tcp...   multi-agent-container
```

### Step 3: Enter the Container

```bash
docker exec -it multi-agent-container /bin/zsh
```

You should see a prompt like:
```
dev@multi-agent-container:/workspace$
```

### Step 4: Initialize Your Workspace

```bash
/app/setup-workspace.sh
```

This will:
- ✅ Copy MCP configurations
- ✅ Install Claude Flow
- ✅ Register all MCP tools
- ✅ Verify the setup

### Step 5: Verify Everything Works

```bash
# Check background services
mcp-status

# List available tools
claude-flow mcp tools
```

## 🎉 Success Indicators

You know everything is working when:

1. `mcp-status` shows:
   ```
   mcp-ws-bridge                    RUNNING   pid 123, uptime 0:05:00
   ```

2. `claude-flow mcp tools` lists tools including:
   - imagemagick-mcp
   - blender-mcp
   - qgis-mcp
   - kicad-mcp
   - ngspice-mcp
   - pbr-generator-mcp

## 🔥 Common First Tasks

### Test ImageMagick Tool

```bash
# Create a test image
echo '{"tool": "create_image", "params": {"width": 100, "height": 100, "color": "blue", "output": "test.png"}}' | python3 ./mcp-tools/imagemagick_mcp.py
```

### Connect External Blender

1. Start Blender with MCP server on port 9876
2. Test connection:
   ```bash
   telnet localhost 9876
   ```

### Explore Available Tools

```bash
# Get detailed tool information
claude-flow mcp tools --verbose
```

## ⚡ Quick Commands Reference

| Command | Description |
|---------|-------------|
| `mcp-status` | Check service status |
| `claude-flow mcp tools` | List all tools |
| `exit` | Leave container |
| `docker exec -it multi-agent-container /bin/zsh` | Re-enter container |
| `docker-compose down` | Stop everything |
| `docker-compose logs -f` | View logs |

## 🆘 Quick Fixes

### "Connection refused" error
```bash
# Start supervisord manually
sudo supervisord -c /etc/supervisor/conf.d/supervisord.conf
```

### "Tool not found" error
```bash
# Re-initialize tools
claude-flow mcp init --file ./.mcp.json
```

### "Permission denied" error
```bash
# Fix ownership
sudo chown -R dev:dev /workspace
```

## 📚 Next Steps

- Read the [Architecture Documentation](./ARCHITECTURE.md)
- Explore the [Full README](./README.md)
- Start building with MCP tools!

---

**Need help?** Check the [Troubleshooting Guide](./README.md#-troubleshooting) or open an issue!