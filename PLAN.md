# MCP Stabilization Plan

This plan outlines the steps to create a stable, headless MCP control plane.

## 1. Remove Graphical Dependencies

-   **File:** `supervisord.conf`
    -   **Action:** Delete the entire `[program:xvfb]` section.
-   **File:** `entrypoint.sh`
    -   **Action:** Delete the lines that start the `Xvfb` process.

## 2. Install Node.js Dependencies

-   **File:** `core-assets/scripts/package.json` (New File)
    -   **Action:** Create this file to define dependencies for the Node.js MCP clients.
    -   **Content:**
        ```json
        {
          "name": "mcp-client-scripts",
          "version": "1.0.0",
          "description": "Dependencies for MCP Node.js client scripts",
          "dependencies": {
            "@modelcontextprotocol/sdk": "^0.2.0"
          }
        }
        ```
-   **File:** `Dockerfile`
    -   **Action:** Add commands to copy the `package.json` and run `npm install`.
    -   **Placement:** Add these lines after copying the `core-assets`.
    -   **Code:**
        ```dockerfile
        COPY core-assets/scripts/package.json /app/core-assets/scripts/
        RUN cd /app/core-assets/scripts && npm install
        ```

## 3. Verify Python Dependencies

-   **File:** `Dockerfile`
    -   **Action:** Ensure the existing `requirements.txt` is installed correctly via `pip`. The current `Dockerfile` seems to be missing this step.
    -   **Placement:** Add after the `COPY requirements.txt` line.
    -   **Code:**
        ```dockerfile
        RUN pip install --no-cache-dir -r requirements.txt
        ```
-   **File:** `requirements.txt`
    -   **Action:** Verify it contains necessary packages for the Python MCP tools (e.g., `websockets`, `zeroconf`). If not, they will need to be added. (This will be a verification step during implementation).

## 4. Final Build and Test

-   **Action:** Execute `./powerdev.sh build && ./powerdev.sh start`.
-   **Verification:** Run `mcp-status` to confirm all clients are `RUNNING`.
-   **Verification:** Run `mcp-test-blender` to confirm the connection.