# Networking Deep Dive

This document provides a detailed explanation of the networking model used in the Multi-Agent Docker Environment.

## 1. Custom Docker Network: `docker_ragflow`

The entire environment operates on a custom Docker bridge network named `docker_ragflow`. This network provides a private and isolated communication channel between the containers, enabling them to resolve each other's addresses using their service names as hostnames.

**Key Characteristics**:
- **Isolation**: Containers on this network are isolated from the host machine's network, except for explicitly published ports.
- **Service Discovery**: Docker's embedded DNS server allows containers to look up the IP address of other containers on the same network using their service names (e.g., `multi-agent-container` can reach `gui-tools-container` at `http://gui-tools-service`).
- **Scalability**: The bridge network design allows for easy addition of new services without complex network configuration.

## 2. Inter-Container Communication

Communication between the `multi-agent-container` and the `gui-tools-container` is primarily achieved via TCP sockets. The MCP bridge tools in the `multi-agent-container` connect to the TCP servers running in the `gui-tools-container`.

### Service Hostnames

The hostnames for the GUI application services are defined as environment variables in the `docker-compose.yml` file for the `multi-agent` service. This allows the bridge clients to dynamically connect to the correct host.

- `BLENDER_HOST=gui-tools-service`
- `QGIS_HOST=gui-tools-service`
- `PBR_HOST=gui-tools-service`

## 3. Port Mapping

The following table details the ports exposed by the environment:

| Port | Service | Container | Purpose |
| :--- | :--- | :--- | :--- |
| `3000` | `multi-agent` | `multi-agent-container` | Claude Flow UI |
| `3002` | `multi-agent` | `multi-agent-container` | MCP WebSocket Bridge for external control |
| `5901` | `gui-tools-service` | `gui-tools-container` | VNC access to the XFCE desktop environment |
| `9876` | `gui-tools-service` | `gui-tools-container` | Blender MCP TCP Server |
| `9877` | `gui-tools-service` | `gui-tools-container` | QGIS MCP TCP Server |
| `9878` | `gui-tools-service` | `gui-tools-container` | PBR Generator MCP TCP Server |

## 4. WebSocket Bridge (`mcp-ws-relay.js`)

The WebSocket bridge provides a crucial link for external systems to interact with the AI agents and tools inside the `multi-agent-container`.

- **File**: `core-assets/scripts/mcp-ws-relay.js`
- **Port**: `3002`
- **Functionality**:
    1. Listens for incoming WebSocket connections.
    2. For each new connection, it spawns a dedicated `claude-flow` process.
    3. It then relays messages between the WebSocket client and the `claude-flow` process's `stdio` streams.
- **Process Management**: This script is managed by `supervisord` to ensure it is always running.

This architecture allows external controllers to seamlessly execute MCP commands without needing direct access to the container's shell, effectively turning any tool into a remotely accessible service.