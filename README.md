# Multi-Agent Docker Environment

[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Claude Flow](https://img.shields.io/badge/Claude_Flow-alpha-purple?style=for-the-badge)](https://github.com/claude-flow/claude-flow)
[![MCP](https://img.shields.io/badge/MCP-Protocol-blue?style=for-the-badge)](https://modelcontextprotocol.io/)
[![Python](https://img.shields.io/badge/Python-3.12-yellow?style=for-the-badge&logo=python)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-22+-green?style=for-the-badge&logo=node.js)](https://nodejs.org/)

A sophisticated, containerized development platform that integrates the **Claude Flow** orchestration engine with a suite of **MCP (Model Context Protocol)** tools and external application bridges. This environment is designed for building and testing complex, AI-driven development workflows.

## 📚 Project Documentation

This project's documentation is organized into several key documents:

| Document | Description |
|---|---|
| 🚀 **[Quick Start Guide](./QUICKSTART.md)** | The fastest way to get the environment up and running. **Start here!** |
| 🏗️ **[Architecture Overview](./ARCHITECTURE.md)** | A detailed breakdown of the system's components and data flows. |
| 🤖 **[Agent Technical Briefing](./AGENT-BRIEFING.md)** | Technical documentation for AI agents operating within this environment. |

## ✨ Key Features

- **Unified Tool Orchestration**: Uses `claude-flow` to manage all tools via a standardized `stdio` protocol.
- **External Application Bridges**: Provides MCP-to-TCP bridges to connect with external applications like Blender and QGIS.
- **Comprehensive Toolset**: Pre-configured tools for image processing, 3D modeling, circuit design, and geospatial analysis.
- **Modern Development Stack**: Includes Python 3.12, Node.js 22+, Rust, and Deno runtimes.
- **Clean & Extensible Architecture**: A clear separation between background services and on-demand, stateless tools.

## 🔧 Core Commands

Use the helper script for all common operations:

| Command | Description |
|---|---|
| `./multi-agent.sh build` | Build the Docker image. |
| `./multi-agent.sh start` | Start the container in the background. |
| `./multi-agent.sh shell` | Open an interactive shell inside the running container. |
| `./multi-agent.sh logs` | View the container's logs. |
| `./multi-agent.sh stop` | Stop and remove the container. |
| `./multi-agent.sh cleanup` | Stop the container and remove all associated volumes. |