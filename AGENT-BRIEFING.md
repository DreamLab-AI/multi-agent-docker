# Agent Technical Briefing

## 1. Mission Objective
Your primary objective is to function as a highly autonomous, collaborative group of AI agents within this unified Docker environment. Your goal is to assist the user with complex software development, data analysis, and systems architecture tasks by leveraging the full suite of tools and MCP services available.

## 2. Core Architecture: Dual-Container and Bridge-Based

This environment utilizes a sophisticated dual-container architecture to separate concerns and optimize resource usage.

-   **`multi-agent-container` (Your Home):** This is the primary container where you, the AI agents, and all the core logic reside. It contains the `claude-flow` orchestrator, all MCP tool clients, and the development runtimes (Python, Node.js, etc.). Your operations are confined to this container.

-   **`gui-tools-container` (The Workshop):** This second container is dedicated to running resource-intensive GUI applications like Blender, QGIS, and the PBR Generator. It is managed separately and you do not have direct access to it.

-   **The Bridge Pattern:** You interact with the applications in the `gui-tools-container` through a **bridge pattern**. The MCP tools like `blender-mcp`, `qgis-mcp`, and `pbr-generator-mcp` are not the tools themselves, but lightweight clients that forward your requests over the network (via TCP) to the actual applications.

## 3. Key Components & Workflow

### 3.1. Workspace Initialization
- **`setup-workspace.sh`:** This is the master script to prepare a new workspace. It copies configurations, initializes `claude-flow`, and sets up the MCP environment based on `.mcp.json`.

### 3.2. Central Configuration
- **`/app/core-assets/mcp.json`:** Defines all available MCP servers. This is the central registry for all services you can interact with.
- **`/app/core-assets/claude-config/`:** Contains all agent and command definitions for `claude-flow`.
- **`/app/core-assets/roo-config/`:** Contains modes and rules for the Roo agent.

### 3.3. MCP Services Ecosystem

Your capabilities are defined by the MCP tools available in your container. These tools fall into two categories:

-   **Direct Tools:** These are self-contained command-line tools that run directly within your container.
    -   `imagemagick-mcp`: For all image manipulation tasks.
    -   `kicad-mcp`: For electronic design automation (EDA).
    -   `ngspice-mcp`: For circuit simulation.

-   **Bridge Tools:** These tools connect to services running in the `gui-tools-container`.
    -   `blender-mcp`: Your interface to the Blender 3D application.
    -   `qgis-mcp`: Your interface to the QGIS geospatial application.
    -   `pbr-generator-mcp`: Your interface to the PBR texture generation service.

## 4. Your Operational Directives

1.  **Workspace is Key:** Always operate within the `/workspace` directory. Ensure it has been initialized with `/app/setup-workspace.sh` at the start of a session.
2.  **Consult the Tool Reference:** The `TOOLS.md` document is your primary reference for understanding the capabilities and parameters of each MCP tool.
3.  **Respect the Bridge:** When using bridge tools (`blender-mcp`, `qgis-mcp`, `pbr-generator-mcp`), remember you are communicating with a remote application. Commands may take longer to execute.
4.  **Diagnose Failures:**
    *   If a **direct tool** fails, check your command's syntax and parameters.
    *   If a **bridge tool** fails, the issue is likely in the `gui-tools-container`. The service might be down or there could be a network issue. You cannot fix this directly, but you can report the failure to the user, mentioning the bridge pattern.
5.  **Leverage the Full Toolchain:** You have a powerful suite of EDA, 2D/3D, and geospatial tools. Analyze the user's request to determine the optimal combination of MCP services to achieve the goal.