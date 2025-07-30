# Blender 4.5 with MCP in Docker

This setup provides a remotely accessible Ubuntu desktop environment with Blender 4.5 LTS and the MCP addon pre-installed.

## Prerequisites

*   Docker and Docker Compose must be installed on your system.
*   You must have a Docker network named `docker_ragflow`. If you don't have one, you can create it with the command: `docker network create docker_ragflow`
*   **For GPU acceleration:** The [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) must be installed on the machine running Docker.

## How to Build and Run

1.  **Navigate to the `blender-docker` directory:**
    ```bash
    cd blender-docker
    ```

2.  **Build and start the container:**
    ```bash
    docker-compose up -d --build
    ```
    This command will build the Docker image and start the container in detached mode.

## How to Connect

1.  **VNC Client:** You will need a VNC client to connect to the remote desktop. RealVNC Viewer or TigerVNC are good options.

2.  **Connect to the VNC Server:**
    *   Open your VNC client.
    *   Enter `<your-docker-host-ip>:5901` as the VNC server address. Replace `<your-docker-host-ip>` with the IP address of the machine running the Docker container.

You should now see the Ubuntu desktop. Blender will be launched automatically.

## Troubleshooting

If you are still unable to connect, it may be due to a firewall on the machine running Docker. Ensure that your firewall is not blocking incoming connections on port 5901.

You can view the container's startup logs to diagnose issues by running the following command:
```bash
docker logs blender_desktop
```

## How to Stop the Container

To stop the container, run the following command in the `blender-docker` directory:

```bash
docker-compose down