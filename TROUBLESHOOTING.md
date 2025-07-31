# Troubleshooting Guide

This guide provides solutions to common issues you might encounter while using the Multi-Agent Docker Environment.

## 1. Networking Issues

Networking problems are common in multi-container setups. Here's how to diagnose them.

### Issue: Connection Refused from a Bridge Tool

If an MCP bridge tool (e.g., `blender-mcp`, `qgis-mcp`) returns a "Connection refused" error, it means the client in the `multi-agent-container` could not reach the server in the `gui-tools-container`.

**Debugging Steps:**

1.  **Verify Both Containers are Running**:
    ```bash
    # Run this on your host machine
    ./multi-agent.sh status
    ```
    Ensure both `multi-agent-container` and `gui-tools-container` are `Up`.

2.  **Check Network Connectivity from Inside the Container**:
    Access the `multi-agent-container` shell:
    ```bash
    ./multi-agent.sh shell
    ```
    Inside the container, use `ping` to test if the service name of the GUI container is resolvable:
    ```bash
    ping gui-tools-service
    ```
    You should see a reply. If not, there's a problem with the Docker network itself.

3.  **Inspect the Docker Network**:
    From your host machine, inspect the `docker_ragflow` network to ensure both containers are attached:
    ```bash
    docker network inspect docker_ragflow
    ```
    Look for the `"Containers"` section in the JSON output. It should list both `multi-agent-container` and `gui-tools-container`.

4.  **Check Container Logs**:
    The issue might be with the server application inside the `gui-tools-container`. Check its logs:
    ```bash
    # Run this on your host machine
    ./multi-agent.sh logs gui-tools-service
    ```
    Look for any error messages from Blender, QGIS, or the PBR generator server.

## 2. VNC Issues

### Issue: Cannot Connect to VNC on `localhost:5901`

If you can't connect to the GUI environment using a VNC client, follow these steps.

1.  **Verify Port Mapping**:
    Run `docker ps` on your host machine and check the `PORTS` column for `gui-tools-container`. It should include `0.0.0.0:5901->5901/tcp`.

2.  **Check VNC Server Logs**:
    The VNC server (`x11vnc`) runs inside the `gui-tools-container`. Check its logs for errors:
    ```bash
    # Run this on your host machine
    ./multi-agent.sh logs gui-tools-service | grep x11vnc
    ```

3.  **Check XFCE and Xvfb Logs**:
    The VNC server depends on the XFCE desktop environment and the Xvfb virtual frame buffer. Check their logs as well:
    ```bash
    # Run this on your host machine
    ./multi-agent.sh logs gui-tools-service
    ```
    Look for errors related to `Xvfb` or `xfce4-session`.

## 3. MCP Tool Issues

### Issue: "Tool not found"

If `claude-flow` or the `mcp-helper.sh` script reports that a tool is not found:

1.  **Verify `.mcp.json`**:
    Inside the `multi-agent-container`, check the contents of `/workspace/.mcp.json`. Ensure the tool is defined correctly.

2.  **Re-run Setup Script**:
    The workspace might be out of sync with the core assets. Re-run the setup script to copy the latest configurations:
    ```bash
    /app/setup-workspace.sh --force
    ```

3.  **Check File Permissions**:
    Ensure the tool's script is executable:
    ```bash
    ls -l /workspace/mcp-tools/