# Multi-Agent Docker Environment

[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Claude Flow](https://img.shields.io/badge/Claude_Flow-alpha-purple?style=for-the-badge)](https://github.com/claude-flow/claude-flow)
[![MCP](https://img.shields.io/badge/MCP-Protocol-blue?style=for-the-badge)](https://modelcontextprotocol.io/)
[![Python](https://img.shields.io/badge/Python-3.12-yellow?style=for-the-badge&logo=python)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-22+-green?style=for-the-badge&logo=node.js)](https://nodejs.org/)

A sophisticated, containerized development platform that integrates **Claude Flow** orchestration with a comprehensive suite of **MCP (Model Context Protocol)** tools. Designed for AI-driven development workflows with support for 3D modeling, image processing, circuit design, geospatial analysis, and PBR texture generation.

## 🚀 Quick Start

```bash
git clone <repository-url> && cd multi-agent-docker
./multi-agent.sh build
./multi-agent.sh start  # Automatically enters container shell
/app/setup-workspace.sh
./mcp-helper.sh test-all
```

## 📚 Project Documentation

| Document | Description |
|---|---|
| 🚀 **[Quick Start Guide](./QUICKSTART.md)** | Get running in 5 minutes - **Start here!** |
| 🏗️ **[Architecture Overview](./ARCHITECTURE.md)** | System components and data flows |
| 🤖 **[Agent Technical Briefing](./AGENT-BRIEFING.md)** | AI agent documentation and capabilities |

## ✨ Key Features

- **🛠️ 6 Integrated MCP Tools**: ImageMagick, Blender, QGIS, KiCad, NGSpice, PBR Generator
- **🔄 Unified Tool Orchestration**: Claude Flow manages all tools via standardized `stdio` protocol
- **🌉 External Application Bridges**: MCP-to-TCP bridges for Blender and QGIS integration
- **🖥️ Modern Development Stack**: Python 3.12, Node.js 22+, Rust, Deno runtimes
- **⚡ Auto-Setup Workspace**: One-command initialization with helper scripts
- **🎯 Claude-Ready**: Automatic knowledge integration for AI agents

## 🛠️ Available MCP Tools

| Tool | Purpose | Capabilities |
|------|---------|--------------|
| **imagemagick-mcp** | Image Processing | Create, resize, manipulate images and graphics |
| **blender-mcp** | 3D Modeling | 3D modeling, rendering, animation via external Blender |
| **qgis-mcp** | Geospatial Analysis | GIS data processing, mapping, spatial analysis |
| **kicad-mcp** | Electronic Design | PCB design, schematic capture, EDA workflows |
| **ngspice-mcp** | Circuit Simulation | SPICE simulation, circuit analysis |
| **pbr-generator-mcp** | PBR Textures | Generate physically-based rendering materials |

## 🔧 Core Commands

| Command | Description |
|---|---|
| `./multi-agent.sh build` | Build the Docker image |
| `./multi-agent.sh start` | Start container (auto-enters shell) |
| `./multi-agent.sh shell` | Enter running container |
| `./multi-agent.sh logs` | View container logs |
| `./multi-agent.sh stop` | Stop and remove container |
| `./multi-agent.sh cleanup` | Full cleanup including volumes |

## 🎯 MCP Helper Commands

After setup, use the helper script for tool management:

| Command | Description |
|---|---|
| `./mcp-helper.sh list-tools` | List all available MCP tools |
| `./mcp-helper.sh test-all` | Test all tools automatically |
| `./mcp-helper.sh run-tool <tool> '<json>'` | Execute specific tool |
| `./mcp-helper.sh claude-instructions` | Get Claude usage guide |