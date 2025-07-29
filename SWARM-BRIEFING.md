# LLM Swarm Briefing: PowerDev Environment

## 1. Mission Objective
Your primary objective is to function as a highly autonomous, collaborative swarm of AI agents within this unified Docker environment. Your goal is to assist the user with complex software development, data analysis, and systems architecture tasks by leveraging the full suite of tools and MCP services available.

## 2. Core Architecture: Decoupled & Centralized
This environment has been refactored to a clean, modular architecture. Key principles are:
- **`core-assets` is the Source of Truth:** All core configurations, agent definitions, and essential scripts are located in `/app/core-assets`. This is the immutable foundation of the environment.
- **Dynamic Workspace:** The `/workspace` directory is ephemeral and user-managed. It is initialized by running `/app/setup-workspace.sh`, which provisions it with the necessary files from `core-assets`. You should always operate within the `/workspace` directory.
- **Externalized Services:** Heavy applications like Blender and QGIS are no longer installed inside this container. Instead, we connect to them as external services via MCP bridges.

## 3. Key Components & Workflow

### 3.1. Workspace Initialization
- **`setup-workspace.sh`:** This is the master script to prepare a new workspace. It copies configurations, initializes `claude-flow`, and sets up the MCP environment based on `.mcp.json`.

### 3.2. Central Configuration
- **`/app/core-assets/mcp.json`:** Defines all available MCP servers. This is the central registry for all services you can interact with.
- **`/app/core-assets/claude-config/`:** Contains all agent and command definitions for `claude-flow`.
- **`/app/core-assets/roo-config/`:** Contains modes and rules for the Roo agent.

### 3.3. MCP Services Ecosystem
The environment is built around a rich ecosystem of MCP servers, managed by `supervisord`. You can interact with:
- **`claude-flow` & `ruv-swarm`:** Core swarm coordination and intelligence.
- **`mcp-ws-bridge`:** A critical WebSocket-to-Stdio bridge on port `3002`. This allows external systems (e.g., a Rust client in another container) to connect and control the `claude-flow` MCP process.
- **Specialized Tool Servers:**
    - `blender-tcp`: Connects to an external Blender instance.
    - `kicad-mcp`: For electronic design automation.
    - `ngspice-mcp`: For circuit simulation.
    - `imagemagick-mcp`: For advanced image manipulation.
    - `pbr-generator-mcp`: For creating physically-based rendering materials.
    - `qgis-mcp`: Connects to an external QGIS instance for geospatial analysis.

## 4. Your Operational Directives
1.  **Assume a Clean Slate:** Always consider the `/workspace` as potentially empty. Your first step in a new session might be to ensure the workspace is initialized.
2.  **Consult `mcp.json`:** Before attempting to use a tool, understand how it's configured in `.mcp.json` (once copied to the workspace). This tells you the command, arguments, and environment variables.
3.  **Use the Bridge for External Control:** The `mcp-ws-bridge` is the designated entry point for external systems to interact with the swarm. All communication should be routed through it.
4.  **Leverage the Full Toolchain:** You have a powerful suite of EDA, 2D/3D, and geospatial tools at your disposal. Analyze the user's request to determine the optimal combination of MCP services to achieve the goal.
5.  **Self-Correction and Adaptation:** If a tool is not available or a connection fails, consult the configuration files and the environment setup to diagnose the issue. The architecture is designed to be transparent and debuggable.