#!/usr/bin/env bash
# powerdev.sh  –  helper for the claude-flow@alpha powered development container
set -euo pipefail

IMAGE=powerdev:latest
NAME=powerdev
ENVFILE=.env     # ← update to match your actual env file

# Source the .env file to make variables available to the script
if [[ -f "${ENVFILE}" ]]; then
  source "${ENVFILE}"
fi

# ---- Resource detection and validation ---------------------
detect_resources() {
  AVAILABLE_CPUS=$(nproc)
  AVAILABLE_MEM=$(free -g | awk '/^Mem:/{print $2}')

  # Set sensible defaults based on available resources
  DEFAULT_CPUS=$((AVAILABLE_CPUS > 24 ? 24 : AVAILABLE_CPUS))
  DEFAULT_MEM=$((AVAILABLE_MEM > 200 ? 200 : AVAILABLE_MEM > 10 ? AVAILABLE_MEM-10 : 4))

  # Apply user overrides or use calculated defaults
  DOCKER_CPUS=${DOCKER_CPUS:-$DEFAULT_CPUS}
  DOCKER_MEMORY=${DOCKER_MEMORY:-${DEFAULT_MEM}g}

  # Validate resources don't exceed available
  if [[ $DOCKER_CPUS -gt $AVAILABLE_CPUS ]]; then
    echo "Warning: Requested CPUs ($DOCKER_CPUS) exceeds available ($AVAILABLE_CPUS)"
    DOCKER_CPUS=$AVAILABLE_CPUS
  fi
}

# ---- Runtime options setup (called after resource detection) ---------------------
setup_run_opts() {
  RUN_OPTS=(
    --gpus all
    --cpus "${DOCKER_CPUS}"
    --memory "${DOCKER_MEMORY}"
    # Balanced security: allow package installation but limit host access
    --security-opt apparmor:unconfined  # Allow package installation
    --security-opt seccomp:unconfined   # Allow system calls needed for development
    --cap-add SYS_ADMIN                 # Required for Docker-in-Docker
    --cap-add SYS_PTRACE                # Required for debugging
    --cap-drop ALL                      # Drop all capabilities first
    --cap-add CHOWN --cap-add DAC_OVERRIDE --cap-add FOWNER --cap-add FSETID --cap-add KILL --cap-add SETGID --cap-add SETUID --cap-add NET_BIND_SERVICE --cap-add NET_RAW --cap-add SYS_CHROOT --cap-add MKNOD --cap-add AUDIT_WRITE --cap-add SETFCAP
    --pids-limit 4096
    -u dev
    --env-file "${ENVFILE}"
    # Mount with proper permissions - all writable by dev user
    -v "${EXTERNAL_DIR:-./.agent-mount/ext}:/workspace/ext:rw"
    -v "./.agent-mount/docker_data:/home/dev/data:rw"
    -v "./.agent-mount/docker_workspace:/home/dev/workspace:rw"
    -v "./.agent-mount/docker_analysis:/home/dev/analysis:rw"
    -v "./.agent-mount/docker_logs:/home/dev/logs:rw"
    -v "./.agent-mount/docker_output:/home/dev/output:rw"
    -v "./.agent-mount/docker_latex:/home/dev/latex:rw"
    # SSH access (read-only for security)
    -v "${HOME}/.ssh:/home/dev/.ssh:ro"
    -v "${SSH_AUTH_SOCK:-/tmp/ssh-agent.sock}:/tmp/ssh-agent.sock:rw"
    -e SSH_AUTH_SOCK=/tmp/ssh-agent.sock
    --network docker_ragflow
    # Docker socket for DinD with group access control
    -v /var/run/docker.sock:/var/run/docker.sock:rw
    --privileged # Required for Docker-in-Docker but constrained by caps
    # Claude Flow web interface
    -p 3000:3000
    # Environment variables for claude-flow
    -e CLAUDE_FLOW_PORT=3000
    -e CLAUDE_FLOW_HOST=0.0.0.0
    -e CLAUDE_FLOW_DATA_DIR=/home/dev/data/claude-flow
  )
}

# ---- Pre-flight checks ---------------------
preflight() {
  # Check Docker daemon
  if ! docker info >/dev/null 2>&1; then
    echo "Error: Docker daemon not accessible"
    exit 1
  fi

  # Check NVIDIA Docker runtime (removed as it was causing false positives; --gpus all is used in run_opts)
  # if ! docker run --rm --gpus all nvidia/cuda:12.9.0-base-ubuntu24.04 nvidia-smi >/dev/null 2>&1; then
  #   echo "Warning: NVIDIA Docker runtime not available or no GPU detected"
  # fi

  # Ensure required directories exist with proper permissions
  mkdir -p "./.agent-mount/docker_data" "./.agent-mount/docker_workspace"
  mkdir -p "./.agent-mount/docker_analysis" "./.agent-mount/docker_logs" "./.agent-mount/docker_output" "./.agent-mount/docker_latex"
  mkdir -p "./.agent-mount/docker_data/claude-flow"  # Claude Flow data directory

  # Create EXTERNAL_DIR if set, otherwise create the default ./.agent-mount/ext
  if [[ -n "${EXTERNAL_DIR}" ]]; then
    mkdir -p "${EXTERNAL_DIR}"
  else
    mkdir -p "./.agent-mount/ext"
  fi

  # Set proper permissions for container user (UID 1000)
  if command -v chown >/dev/null 2>&1; then
    chown -R 1000:1000 "./.agent-mount/" 2>/dev/null || echo "Warning: Could not set ownership (this is normal on some systems)"
  fi

  # Ensure directories are writable
  chmod -R 755 "./.agent-mount/"

  echo "Created persistent directories:"
  echo "  - ./.agent-mount/docker_data (general data)"
  echo "  - ./.agent-mount/docker_data/claude-flow (claude-flow data)"
  echo "  - ./.agent-mount/docker_workspace (workspace files)"
  echo "  - ./.agent-mount/docker_analysis (analysis outputs)"
  echo "  - ./.agent-mount/docker_logs (container logs)"
  echo "  - ./.agent-mount/docker_output (processing outputs)"
  echo "  - ./.agent-mount/docker_latex (LaTeX projects)"
  if [[ -n "${EXTERNAL_DIR}" ]]; then
    echo "  - ${EXTERNAL_DIR} (external files)"
  else
    echo "  - ./.agent-mount/ext (external files)"
  fi

  # Create network if it doesn't exist
  if ! docker network inspect docker_ragflow >/dev/null 2>&1; then
    echo "Creating docker_ragflow network..."
    docker network create docker_ragflow
  fi

  # Validate config
  validate_config
}

# ---- Config validation ---------------------
validate_config() {
  if [[ ! -f "$ENVFILE" ]]; then
    echo "Warning: $ENVFILE not found - using environment variables only"
  fi

  if [[ -z "$EXTERNAL_DIR" ]]; then
    echo "Warning: EXTERNAL_DIR not set - using default path"
  fi
}


ensure_claude_md() {
  if [[ ! -f "CLAUDE-README.md" ]]; then
    echo "CLAUDE-README.md not found. Creating it..."
    cat > CLAUDE-README.md <<'CLAUDE_MD_EOF'
# CLAUDE-README.md — Boot Guide (Claude Code v4 + Claude Flow Alpha)

## 1. CORE DIRECTIVES
1. **Prod-ready only** – ship runnable code; no TODOs or stubs.
2. **Token-efficient reasoning** – think silently; output final answer unless asked.
3. **Edge-case first** – list boundaries → write tests → implement.
4. **Selective context pull** – fetch only needed paths + line nums in large repos.
5. **Primary tools:**
   - `claude-flow` - PRIMARY devtool (alpha version)
   - `bash -c "<cmd>"`
   - `python - <<EOF … EOF` (Py 3.12 default)
   - `ruv-swarm` MCP (supporting agent orchestration)
6. **No hedging / flattery / chit-chat.**

## 2. ENVIRONMENT SNAPSHOT

| Layer | Key Items |
|-------|-----------|
| **HW** | Auto-detected CPU/RAM / NVMe / NVIDIA GPUs |
| **Python 3.12** | `torch` 2.7+ + CUDA 12.9, `tensorflow`, `keras`, `xgboost`, `wgpu` |
| **Python 3.13** | Clean sandbox (`pip`, `setuptools`, `wheel`) |
| **CUDA + cuDNN** | `/usr/local/cuda` ready |
| **Rust** | `rustup`, `clippy`, `cargo-edit`, `sccache` |
| **Node 22 LTS** | PRIMARY: `claude-flow@alpha`, supporting: `ruv-swarm` |
| **Linters** | `shellcheck`, `flake8`, `pylint`, `hadolint` |
| **LaTeX** | `texlive-full`, `latexmk`, `chktex` |
| **Extras** | `tmux`, `hyperfine`, `docker`, `WasmEdge`, `OpenVINO`, `Modular MAX` |
| **Web UI** | Claude-Flow UI → **http://localhost:3000** (PRIMARY INTERFACE) |

### Quick env switches:
```bash
source /opt/venv312/bin/activate   # ML env
source /opt/venv313/bin/activate   # Py 3.13 sandbox
```

## 3. PRIMARY TOOLS & SYNTAX

### 3.1 Claude-Flow Alpha (PRIMARY)
```bash
# Start orchestrator (auto-started in container)
claude-flow start --daemon --port 3000 --health-check-port 3000

# Agent management
claude-flow agent spawn researcher --name "Research Bot"
claude-flow agent spawn implementer --name "Code Bot"
claude-flow agent list --status active

# Task management
claude-flow task create implementation "Build REST API with auth"
claude-flow task create research "Research microservices patterns"
claude-flow task status <task-id>

# Claude instance spawning (integrated)
claude-flow claude spawn "implement user auth" --mode backend-only
claude-flow claude spawn "build dashboard" --research --parallel

# Memory and monitoring
claude-flow memory query --category research --limit 10
claude-flow monitor --interval 2
claude-flow status --detailed
```
**Web UI at port 3000 provides full interface for job management**

### 3.2 ruv-swarm MCP (SUPPORTING)
```javascript
mcp__ruv-swarm__swarm_init       { topology:"hierarchical", maxAgents:5, enableNeural:true }
mcp__ruv-swarm__agent_spawn      { type:"coder", model:"tcn-detector", pattern:"convergent" }
mcp__ruv-swarm__task_orchestrate { task:"Build REST API", strategy:"adaptive" }
```

### 3.3 LaTeX Environment
- **Full Distribution**: `texlive-full` is installed.
- **Build Tool**: Use `latexmk` for easy compilation.
- **Linter**: Use `chktex` to check for common errors.

Example workflow in `/home/dev/latex`:
```bash
# Create a simple document
echo '\documentclass{article}\begin{document}Hello, LaTeX!\end{document}' > mydoc.tex

# Compile it
latexmk -pdf mydoc.tex

# Clean up auxiliary files
latexmk -c
```

## 4. STRUCTURED OUTPUT CONTRACT
Return one of:
- **diff** – patch for `git apply`
- **bash** – shell commands
- **text** – plain explanation

Always end with **✅ Done** so orchestrator can detect completion.

## 5. CODING & STYLE STANDARDS
- **Language picks:** Py 3.12 for ML; Rust for perf; Node 22 for CLIs.
- **Tests:** `pytest -q`, `cargo test`, edge cases mandatory.
- **Formatters:** `black`, `ruff`, `rustfmt`, `prettier`.
- **Docs:** Public APIs need docstrings + one example.
- **Forbidden:** long apologies, empty sections, unexplained "maybe".

## 6. COMMON WORKFLOWS

| Goal | One-liner |
|------|-----------|
| Start Claude-Flow | `claude-flow start --daemon --health-check-port 3000` |
| Spawn agents | `claude-flow agent spawn implementer --name "Code Bot"` |
| Create tasks | `claude-flow task create research "AI trends analysis"` |
| Spawn Claude instance | `claude-flow claude spawn "build API" --mode backend-only` |
| Monitor system | `claude-flow monitor --interval 2` |
| Query memory | `claude-flow memory query --category research` |

## 7. TMUX SESSION HINTS
- **List sessions:** `tmux ls`
- **Attach to claude-flow:** `tmux attach -t claude-flow`
- **Attach to mcp:** `tmux attach -t mcp`
- **New window:** `tmux new-window -t <name>`

## 8. CONTAINER SETUP
- **Port 3000:** Claude-Flow web UI (primary interface)
- **Data directory:** `/home/dev/data/claude-flow`
- **Workspace:** `/workspace` (mounted from host)
- **External files:** `/workspace/ext` (mounted from host)

## 9. UPDATE RULES
- Keep file ≤ 350 lines; prune every quarter.
- Update Environment Snapshot on image changes.
- Append new claude-flow commands when alpha versions update.

---

### Next steps
1. Access web UI at http://localhost:3000
2. Use `claude-flow status` to check system health
3. Spawn agents with `claude-flow agent spawn <type>`
4. Create tasks with `claude-flow task create <type> "description"`

CLAUDE_MD_EOF
    echo "CLAUDE-README.md created successfully."
  fi
}

help() {
  cat <<EOF
Usage: $0 {build|start|daemon|exec|logs|health|stop|rm|restart|watch|status|cleanup|persist|debug}

  build        Build the Docker image:
                 $0 build

  start        Run or start the container with hardened flags (interactive):
                 $0 start

  daemon       Run the container in background mode (detached):
                 $0 daemon

  exec CMD     Run a command inside the running container:
                 $0 exec bash

  logs         Tail container logs:
                 $0 logs

  health       Show container health status:
                 $0 health

  status       Show detailed container status:
                 $0 status

  stop         Stop the container:
                 $0 stop

  rm           Remove the container:
                 $0 rm

  restart      Restart the container:
                 $0 restart

  watch        Loop, checking health every 60s and restarting if unhealthy:
                 $0 watch

  cleanup      Clean up Docker resources (system and volume prune):
                 $0 cleanup

  persist      Save analysis outputs to persistent storage:
                 $0 persist

  debug        Start the container with an interactive shell for debugging:
                 $0 debug

Data Persistence:
  - Analysis outputs: ./.agent-mount/docker_analysis/
  - Container logs: ./.agent-mount/docker_logs/
  - Processing outputs: ./.agent-mount/docker_output/
  - LaTeX projects: ./.agent-mount/docker_latex/
  - Workspace files: ./.agent-mount/docker_workspace/
  - General data: ./.agent-mount/docker_data/
  - External files: ./.agent-mount/ext/
EOF
}

build() {
  preflight
  detect_resources
  ensure_claude_md

  # Validate Dockerfile if hadolint is available
  if command -v hadolint >/dev/null 2>&1; then
    echo "Linting Dockerfile..."
    hadolint Dockerfile || echo "Warning: Dockerfile linting failed"
  fi

  export DOCKER_BUILDKIT=1
  docker build \
    --network=host \
    --progress=plain \
    --secret id=GH_TOKEN,env=GH_TOKEN \
    -t "$IMAGE" . "${@:2}"
}

start() {
  detect_resources
  setup_run_opts

  if docker ps -a --format '{{.Names}}' | grep -q "^${NAME}$"; then
    docker start -ai "$NAME"
  else
    docker run "${RUN_OPTS[@]}" --name "$NAME" -it "$IMAGE"
  fi
}

daemon() {
  detect_resources
  setup_run_opts

  if docker ps -a --format '{{.Names}}' | grep -q "^${NAME}$"; then
    echo "Starting existing container in background..."
    docker start "$NAME"
  else
    echo "Creating new container in background..."
    docker run "${RUN_OPTS[@]}" --name "$NAME" -d "$IMAGE"
  fi

  echo "Container '$NAME' running in background"
  echo "Access with: $0 exec bash"
  echo "View logs with: $0 logs"
  echo "Web UI available at: http://localhost:3000"
}

persist() {
  if ! docker ps --format '{{.Names}}' | grep -q "^${NAME}$"; then
    echo "Error: Container '$NAME' is not running"
    return 1
  fi

  echo "Saving analysis outputs to persistent storage..."

  # Create timestamped backup directory
  TIMESTAMP=$(date +%Y%m%d_%H%M%S)
  BACKUP_DIR="./.agent-mount/docker_analysis/backup_${TIMESTAMP}"
  mkdir -p "$BACKUP_DIR"

  # Copy container analysis data
  docker cp "$NAME:/home/dev/analysis/." "$BACKUP_DIR/" 2>/dev/null || echo "No analysis data found"
  docker cp "$NAME:/home/dev/output/." "./.agent-mount/docker_output/" 2>/dev/null || echo "No output data found"

  # Export container logs
  docker logs "$NAME" > "./.agent-mount/docker_logs/container_${TIMESTAMP}.log"

  # Export container state
  docker inspect "$NAME" > "${BACKUP_DIR}/container_state.json"

  echo "Data saved to:"
  echo "  - Analysis: $BACKUP_DIR/"
  echo "  - Outputs: ./.agent-mount/docker_output/"
  echo "  - Logs: ./.agent-mount/docker_logs/container_${TIMESTAMP}.log"
  echo "  - State: $BACKUP_DIR/container_state.json"
}

exec() {
  if ! docker ps --format '{{.Names}}' | grep -q "^${NAME}$"; then
    echo "Error: Container '$NAME' is not running"
    return 1
  fi
  docker exec -it -u dev "$NAME" "${@:2}"
}

logs() {
  docker logs -f "$NAME"
}

health() {
  docker inspect --format='{{.State.Health.Status}}' "$NAME"
}

stop() {
  docker stop "$NAME"
}

rm() {
  docker rm "$NAME"
}

restart() {
  # Use docker restart for idempotency. It works if the container is running or stopped.
  docker restart "$NAME"
}

status() {
  if docker ps -a --format '{{.Names}}' | grep -q "^${NAME}$"; then
    echo "Container Status:"
    docker ps -a --filter "name=^${NAME}$" --format "table {{.Names}}\t{{.Status}}\t{{.State}}"
    echo -e "\nHealth: $(health || echo 'N/A')"
    echo "Ports: $(docker port "$NAME" 2>/dev/null || echo 'None')"
    echo "Image: $(docker inspect --format='{{.Config.Image}}' "$NAME" 2>/dev/null || echo 'N/A')"
    echo "Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" "$NAME" 2>/dev/null || echo "  Stats not available"
  else
    echo "Container '$NAME' does not exist"
  fi
}

cleanup() {
  echo "Cleaning up Docker resources..."
  docker system prune -f
  docker volume prune -f
  echo "Cleanup complete"
}

watch() {
  echo "Watching health for ${NAME}…"
  while sleep 60; do
    if ! docker ps --format '{{.Names}}' | grep -q "^${NAME}$"; then
      echo "$(date) - Container not found, exiting watch"
      break
    fi
    status_check=$(health || echo "none")
    if [[ "$status_check" != "healthy" ]]; then
      echo "$(date) - Container unhealthy ($status_check), restarting…"
      restart
      sleep 10  # Give container time to start
    fi
  done
}

# ---- Shell completion ---------------------
_powerdev_completion() {
  COMPREPLY=($(compgen -W "build start daemon exec logs health status stop rm restart watch cleanup persist" -- "${COMP_WORDS[COMP_CWORD]}"))
}
complete -F _powerdev_completion powerdev.sh

# ---- Graceful shutdown handler ---------------------
trap 'echo "Shutting down..."; stop 2>/dev/null; exit' SIGINT SIGTERM

debug() {
  detect_resources
  setup_run_opts

  docker run "${RUN_OPTS[@]}" --entrypoint /bin/bash --name "$NAME-debug" -it "$IMAGE"
}

# Entry point
if [[ $# -eq 0 ]]; then
  help
  exit 1
fi

case $1 in
  build|start|daemon|exec|logs|health|status|stop|rm|restart|watch|cleanup|persist|debug)
    "$@"
    ;;
  *)
    help
    ;;
esac