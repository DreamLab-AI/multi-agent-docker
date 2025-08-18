#!/usr/bin/env bash
# multi-agent.sh - helper for the multi-agent docker environment
set -euo pipefail

# Configuration
COMPOSE_FILE=docker-compose.yml
PROJECT_NAME=multi-agent
CONTAINER_NAME=multi-agent-container
ENVFILE=.env
IMAGE=multi-agent-docker:latest

# Source the .env file to make variables available to the script
if [[ -f "${ENVFILE}" ]]; then
  source "${ENVFILE}"
fi

# ---- Resource detection and validation ---------------------
detect_resources() {
  AVAILABLE_CPUS=$(nproc)
  AVAILABLE_MEM=$(free -g | awk '/^Mem:/{print $2}')

  # Set sensible defaults based on available resources
  DEFAULT_CPUS=$AVAILABLE_CPUS
  DEFAULT_MEM=$((AVAILABLE_MEM - 2)) # Leave 2GB for the host OS

  # Apply user overrides or use calculated defaults
  DOCKER_CPUS=${DOCKER_CPUS:-$DEFAULT_CPUS}
  DOCKER_MEMORY=${DOCKER_MEMORY:-${DEFAULT_MEM}g}

  # Validate resources don't exceed available
  if [[ $DOCKER_CPUS -gt $AVAILABLE_CPUS ]]; then
    echo "Warning: Requested CPUs ($DOCKER_CPUS) exceeds available ($AVAILABLE_CPUS)"
    DOCKER_CPUS=$AVAILABLE_CPUS
  fi
}

# ---- Pre-flight checks ---------------------
preflight() {
  # Check Docker daemon
  if ! docker info >/dev/null 2>&1; then
    echo "Error: Docker daemon not accessible"
    exit 1
  fi

  # Check docker-compose
  if ! command -v docker-compose >/dev/null 2>&1; then
    echo "Error: docker-compose not found. Please install docker-compose"
    exit 1
  fi

  # Ensure required directories exist with proper permissions
  # These directories are mounted as volumes in docker-compose.yml
  mkdir -p "./workspace"
  mkdir -p "./blender-files"
  mkdir -p "./pbr_outputs"
  # Create EXTERNAL_DIR if set
  if [[ -n "${EXTERNAL_DIR:-}" ]]; then
    mkdir -p "${EXTERNAL_DIR}"
  else
    mkdir -p "./.agent-mount/ext"
  fi

  # Set proper permissions for container user
  # Use variables from .env file, with 1000 as a fallback
  if command -v chown >/dev/null 2>&1; then
    chown -R "${HOST_UID:-1000}:${HOST_GID:-1000}" "./workspace" "./blender-files" "./pbr_outputs" "./.agent-mount" 2>/dev/null || echo "Warning: Could not set ownership (this is normal on some systems)"
  fi

  # Ensure directories are writable
  chmod -R 775 "./workspace" "./blender-files" "./pbr_outputs" "./.agent-mount"

  echo "Created persistent directories"

  # Detect resources before creating .env
  detect_resources

  # Create .env file if it doesn't exist
  if [[ ! -f "$ENVFILE" ]]; then
    echo "Creating default .env file..."
    cat > "$ENVFILE" <<EOF
# User/Group IDs for file permissions
HOST_UID=$(id -u)
HOST_GID=$(id -g)

# Resource limits
DOCKER_CPUS=$DOCKER_CPUS
DOCKER_MEMORY=$DOCKER_MEMORY

# External directory for mounted files
EXTERNAL_DIR=./.agent-mount/ext

# MCP Configuration
REMOTE_MCP_HOST=
MCP_LOG_LEVEL=debug
POLL_INTERVAL=5000

# Grafana password
GRAFANA_PASSWORD=admin

EOF
    echo ".env file created with defaults"
  fi

  # Validate config
  validate_config
}

# ---- Config validation ---------------------
validate_config() {
  if [[ ! -f "$COMPOSE_FILE" ]]; then
    echo "Error: $COMPOSE_FILE not found"
    exit 1
  fi

  if [[ ! -f "$ENVFILE" ]]; then
    echo "Warning: $ENVFILE not found - using environment variables only"
  fi
}

# ---- Help message ---------------------
help() {
  cat <<EOF
Usage: $0 {build|start|stop|restart|status|logs|shell|cleanup}

Multi-Agent Docker Commands:

  build                Build the Docker image:
                       $0 build

  start                Start the container:
                       $0 start

  stop                 Stop the container:
                       $0 stop

  restart              Restart the container:
                       $0 restart

  status               Show container status:
                       $0 status

  logs                 View container logs:
                       $0 logs
                       $0 logs -f          # Follow logs

  shell                Open shell in container:
                       $0 shell

  cleanup              Clean up container and volumes:
                       $0 cleanup

Service URLs:
  - Claude Flow UI: http://localhost:3000
  - MCP WebSocket: ws://localhost:3002
  - MCP TCP Server: tcp://localhost:9500
EOF
}

# ---- Build command ---------------------
build() {
  echo "Building multi-agent docker image..."
  docker-compose -f "$COMPOSE_FILE" build
  echo "Build complete!"
}

# ---- Start command ---------------------
start() {
  echo "Starting multi-agent container..."
  docker-compose -f "$COMPOSE_FILE" up -d

  echo ""
  echo "Container started! Waiting for health checks..."
  sleep 5

  # Show status
  status

  echo ""
  echo "Access points:"
  echo "  - Claude Flow UI: http://localhost:3000"
  echo "  - MCP WebSocket: ws://localhost:3002"
  echo "  - MCP TCP Server: tcp://localhost:9500"

  # Automatically enter the shell
  shell
}

# ---- Stop command ---------------------
stop() {
  echo "Stopping multi-agent container..."
  docker-compose -f "$COMPOSE_FILE" down
  echo "Container stopped."
}

# ---- Restart command ---------------------
restart() {
  stop
  sleep 2
  start "$@"
}

# ---- Status command ---------------------
status() {
  echo "Multi-Agent Container Status:"
  echo "============================="
  docker-compose -f "$COMPOSE_FILE" ps
}

# ---- Logs command ---------------------
logs() {
  docker-compose -f "$COMPOSE_FILE" logs "$@"
}

# ---- Shell command ---------------------
shell() {
  echo "Entering multi-agent container as 'dev' user..."
  docker exec -it -u dev "$CONTAINER_NAME" /bin/bash
}


# ---- Cleanup command ---------------------
cleanup() {
  echo "This will remove the container and volumes. Are you sure? (y/N)"
  read -r response

  if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "Stopping and removing container..."
    docker-compose -f "$COMPOSE_FILE" down -v
    echo "Cleanup complete."
  else
    echo "Cleanup cancelled."
  fi
}


# ---- Graceful shutdown handler ---------------------
trap 'echo "Shutting down..."; stop 2>/dev/null; exit' SIGINT SIGTERM

# ---- Main entry point ---------------------
if [[ $# -eq 0 ]]; then
  help
  exit 1
fi

case $1 in
  build|start|stop|restart|status|logs|shell|cleanup)
    "$1"
    ;;
  *)
    help
    exit 1
    ;;
esac