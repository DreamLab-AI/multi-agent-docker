#!/bin/bash
# Enhanced setup script for the Multi-Agent Docker Environment
#
# Features:
# - Non-destructive and idempotent operations
# - Argument parsing for --dry-run, --force, --quiet
# - Additive merging of .mcp.json configurations
# - Unified toolchain PATH setup (/etc/profile.d)
# - Rust toolchain validation and repair
# - Supervisorctl-based aliases for service management
# - Appends a compact, informative context section to CLAUDE.md

# --- Argument Parsing ---
DRY_RUN=false
FORCE=false
QUIET=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --quiet)
            QUIET=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# --- Logging Functions ---
log_info() {
    [ "$QUIET" = false ] && echo "ℹ️  $1"
}

log_success() {
    [ "$QUIET" = false ] && echo "✅ $1"
}

log_warning() {
    [ "$QUIET" = false ] && echo "⚠️  $1"
}

log_error() {
    echo "❌ $1" >&2
}

dry_run_log() {
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] $1"
        return 0
    fi
    return 1
}

# --- Sudo Check ---
if [ "$(id -u)" -ne 0 ] && [ "$DRY_RUN" = false ]; then
    log_info "Requesting root privileges for setup..."
    exec sudo /bin/bash "$0" "$@"
fi

echo "🚀 Initializing enhanced Multi-Agent workspace..."
[ "$DRY_RUN" = true ] && echo "🔍 DRY RUN MODE - No changes will be made"

# --- Claude Code Home Directory Workaround ---
log_info "Applying workaround for Claude Code home directory..."
if [ ! -d "/home/ubuntu" ]; then
    if dry_run_log "Would create symlink /home/ubuntu -> /home/dev"; then :; else
        ln -s /home/dev /home/ubuntu
        log_success "Created symlink /home/ubuntu -> /home/dev for Claude Code compatibility."
    fi
else
    log_info "Directory /home/ubuntu already exists, skipping symlink."
fi

# --- Helper Functions for File Operations ---
copy_if_missing() {
    local src="$1"
    local dest="$2"
    local make_executable="${3:-false}"

    if [ -f "$dest" ] && [ "$FORCE" = false ]; then
        log_info "Skipping $dest (already exists)"
        return 0
    fi

    if dry_run_log "Would copy $src -> $dest"; then return 0; fi

    if [ -f "$src" ]; then
        cp "$src" "$dest" 2>/dev/null || { log_error "Failed to copy $src to $dest"; return 1; }
        [ "$make_executable" = true ] && chmod +x "$dest" 2>/dev/null
        log_success "Copied $src -> $dest"
    else
        log_warning "Source file not found: $src"
    fi
}

copy_dir_contents_if_missing() {
    local src_dir="$1"
    local dest_dir="$2"

    if [ ! -d "$src_dir" ]; then log_warning "Source directory not found: $src_dir"; return 1; fi
    if dry_run_log "Would create directory $dest_dir and copy contents from $src_dir"; then return 0; fi
    mkdir -p "$dest_dir"

    for item in "$src_dir"/*; do
        local dest_item="$dest_dir/$(basename "$item")"
        if [ ! -e "$dest_item" ] || [ "$FORCE" = true ]; then
             if dry_run_log "Would copy $item -> $dest_item"; then continue; fi
            cp -r "$item" "$dest_item"
            log_success "Copied $item -> $dest_item"
        else
            log_info "Skipping $dest_item (already exists)"
        fi
    done
}

# --- Main Setup Logic ---

# 1. Non-destructive copy of essential assets
log_info "📂 Syncing essential assets and helper scripts..."
copy_dir_contents_if_missing "/app/core-assets/mcp-tools" "./mcp-tools"
copy_dir_contents_if_missing "/app/core-assets/scripts" "./scripts"
copy_if_missing "/app/mcp-helper.sh" "./mcp-helper.sh" true

# 2. Non-destructive .mcp.json merge
merge_mcp_json() {
    local src="/app/core-assets/mcp.json"
    local dest="./.mcp.json"
    local backup="${dest}.bak.$(date +%Y%m%d_%H%M%S)"

    if [ ! -f "$src" ]; then log_error "Source MCP config not found: $src"; return 1; fi
    if [ ! -f "$dest" ]; then
        if dry_run_log "Would copy $src -> $dest (new file)"; then return 0; fi
        cp "$src" "$dest"
        log_success "Created new MCP config: $dest"
        return 0
    fi

    if dry_run_log "Would backup $dest -> $backup"; then :; else
        cp "$dest" "$backup"
        log_info "Backed up existing config to $backup"
    fi

    if ! command -v jq >/dev/null 2>&1; then
        log_warning "jq not found. Overwriting .mcp.json as fallback."
        if dry_run_log "Would copy $src -> $dest (jq not found)"; then return 0; fi
        cp "$src" "$dest"
        return 0
    fi

    if dry_run_log "Would merge MCP configs using jq: $src into $dest"; then return 0; fi
    jq -s '.[0] * .[1]' "$dest" "$src" > "${dest}.tmp" && mv "${dest}.tmp" "$dest"
    log_success "Merged MCP configurations into $dest"
}

merge_mcp_json

# 3. Setup enhanced PATH for all toolchains
setup_toolchain_paths() {
    local profile_script="/etc/profile.d/multi-agent-paths.sh"
    if dry_run_log "Would create/update $profile_script"; then return 0; fi
    log_info "🛠️  Setting up enhanced PATH for toolchains..."

    cat > "$profile_script" << 'EOF'
#!/bin/sh
prepend_path() {
    if [ -d "$1" ] && ! echo "$PATH" | grep -q -s "$1"; then
        export PATH="$1:$PATH"
    fi
}
prepend_path "/home/dev/.cargo/bin"
prepend_path "/opt/venv312/bin"
prepend_path "/home/dev/.npm-global/bin"
prepend_path "/home/dev/.local/bin"
prepend_path "/home/dev/.deno/bin"
prepend_path "/opt/oss-cad-suite/bin"
EOF

    chmod +x "$profile_script"
    log_success "Created toolchain PATH configuration: $profile_script"
}

setup_toolchain_paths

# 4. Update bashrc with supervisorctl-based aliases
add_mcp_aliases() {
    local bashrc_file="/home/dev/.bashrc"
    local marker="# MCP Server Management (supervisorctl-based)"

    if [ ! -f "$bashrc_file" ]; then
        if dry_run_log "Would create empty .bashrc for dev user"; then :; else
            sudo -u dev touch "$bashrc_file"
            log_info "Created empty .bashrc for dev user."
        fi
    fi

    if grep -q "$marker" "$bashrc_file"; then
        log_info "MCP aliases already exist in bashrc"
        return 0
    fi

    if dry_run_log "Would add MCP aliases to $bashrc_file"; then return 0; fi

    read -r -d '' BASHRC_ADDITIONS << 'EOF'

# MCP Server Management (supervisorctl-based)
alias mcp-tcp-start='supervisorctl -c /etc/supervisor/conf.d/supervisord.conf start mcp-tcp-server'
alias mcp-tcp-stop='supervisorctl -c /etc/supervisor/conf.d/supervisord.conf stop mcp-tcp-server'
alias mcp-tcp-status='supervisorctl -c /etc/supervisor/conf.d/supervisord.conf status mcp-tcp-server'
alias mcp-tcp-restart='supervisorctl -c /etc/supervisor/conf.d/supervisord.conf restart mcp-tcp-server'
alias mcp-tcp-logs='tail -f /app/mcp-logs/mcp-tcp-server.log'
alias mcp-ws-start='supervisorctl -c /etc/supervisor/conf.d/supervisord.conf start mcp-ws-bridge'
alias mcp-ws-stop='supervisorctl -c /etc/supervisor/conf.d/supervisord.conf stop mcp-ws-bridge'
alias mcp-ws-status='supervisorctl -c /etc/supervisor/conf.d/supervisord.conf status mcp-ws-bridge'
alias mcp-ws-restart='supervisorctl -c /etc/supervisor/conf.d/supervisord.conf restart mcp-ws-bridge'
alias mcp-ws-logs='tail -f /app/mcp-logs/mcp-ws-bridge.log'

# Claude Code Aliases
alias dsp='claude --dangerously-skip-permissions'

# Quick MCP testing functions
mcp-test-tcp() {
    local port=${1:-9500}
    echo "Testing MCP TCP connection on port $port..."
    echo '{"jsonrpc":"2.0","id":"test","method":"tools/list","params":{}}' | nc -w 2 localhost $port
}
mcp-test-health() {
    echo "Testing MCP health endpoint..."
    curl -s http://127.0.0.1:9501/health | jq . 2>/dev/null || curl -s http://127.0.0.1:9501/health
}

# Toolchain validation function
validate-toolchains() {
    echo "=== Toolchain Validation ==="
    printf "Rust cargo: "
    if command -v cargo >/dev/null; then cargo --version; else echo "Not found"; fi
    printf "Python venv: "
    if command -v python >/dev/null; then python --version; else echo "Not found"; fi
    printf "Node.js: "
    if command -v node >/dev/null; then node --version; else echo "Not found"; fi
    printf "Deno: "
    if command -v deno >/dev/null; then deno --version | head -n 1; else echo "Not found"; fi
    printf "JQ: "
    if command -v jq >/dev/null; then jq --version; else echo "Not found"; fi
}
EOF

    sudo -u dev bash -c "echo \"\$1\" >> \"\$2\"" -- "$BASHRC_ADDITIONS" "$bashrc_file"
    log_success "Added MCP management aliases to bashrc"
}

add_mcp_aliases

# 5. Validate and fix Rust toolchain availability
validate_rust_toolchain() {
    log_info "🦀 Validating Rust toolchain availability..."

    log_info_def=$(declare -f log_info)

    sudo -u dev bash -c "
        ${log_info_def}

        source /etc/profile.d/multi-agent-paths.sh
        if [ -f \"\$HOME/.cargo/env\" ]; then source \"\$HOME/.cargo/env\"; fi

        if ! command -v cargo >/dev/null 2>&1; then
            log_info \"Cargo not found, attempting to reinstall Rust toolchain...\"
            if curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path; then
                source \"\$HOME/.cargo/env\"
                log_info \"Rust toolchain reinstalled.\"
            else
                echo \"❌ Failed to reinstall Rust toolchain\"
            fi
        fi

        log_info \"Rustc: \$(rustc --version)\"
        log_info \"Cargo: \$(cargo --version)\"
    "
}

if [ "$DRY_RUN" = false ]; then
    validate_rust_toolchain
else
    dry_run_log "Would validate Rust toolchain"
fi

# 6. Update CLAUDE.md with service and context info
update_claude_md() {
    local claude_md="./CLAUDE.md"
    local marker="## 🔌 Additional Services & Development Context"

    if [ "${SETUP_APPEND_CLAUDE_DOC:-true}" != "true" ]; then
        log_info "Skipping CLAUDE.md updates (SETUP_APPEND_CLAUDE_DOC is not 'true')"
        return 0
    fi

    if [ ! -f "$claude_md" ]; then
        log_warning "CLAUDE.md not found, cannot append info."
        return 1
    fi

    if grep -q "$marker" "$claude_md"; then
        log_info "CLAUDE.md already contains additional services info"
        return 0
    fi

    if dry_run_log "Would append service and context info to $claude_md"; then return 0; fi

    cat >> "$claude_md" << 'EOF'

## 🔌 Additional Services & Development Context

This environment is enhanced with several services and a specific development workflow.

### MCP Services Available
- **TCP Server**: `localhost:9500` for external controllers.
- **WebSocket Bridge**: `localhost:3002` for browser-based tools.
- **Health Check**: `localhost:9501/health` for service monitoring.
- **GUI Tools**: via `gui-tools-service` (Blender:9876, QGIS:9877, PBR:9878).

### Development Context
- **Project Root**: Your project is mounted at `ext/`.
- **Always read the current state of ext/task.md**
- **Always update task.md with your progress, removing elements that are confirmed as working by the user**
- **Execution Environment**: Claude operates within this Docker container. It cannot build external Docker images or see services running on your host machine.
- **Available Toolchains**: You can validate your code using tools inside this container, such as `cargo check`, `npm test`, or `python -m py_compile`.

### Quick Commands
```bash
# Check code without a full build
cargo check         # For Rust projects in ext/
npm run test        # For Node.js projects in ext/

# Manage and test MCP services
mcp-tcp-status
mcp-test-health
validate-toolchains
```
EOF
    log_success "Appended service and context info to CLAUDE.md"
}

update_claude_md

# 7. Patch MCP server to fix hardcoded version, method routing, and agent tracking
patch_mcp_server() {
    log_info "🔧 Patching MCP server to fix version, method routing, and agent tracking..."

    # Ensure claude-flow is installed/updated
    if ! command -v claude-flow >/dev/null 2>&1; then
        log_info "Installing claude-flow@alpha globally..."
        npm install -g claude-flow@alpha || {
            log_warning "Failed to install claude-flow, attempting with sudo..."
            sudo npm install -g claude-flow@alpha || {
                log_error "Failed to install claude-flow"
                return 1
            }
        }
    else
        # Check version and update if needed
        local current_version=$(claude-flow --version 2>/dev/null || echo "unknown")
        log_info "Current claude-flow version: $current_version"

        # Optionally update to latest alpha
        if [[ "$UPDATE_CLAUDE_FLOW" == "true" ]]; then
            log_info "Updating claude-flow to latest alpha..."
            npm update -g claude-flow@alpha || sudo npm update -g claude-flow@alpha
        fi
    fi

    # Find the MCP server file - check multiple locations
    local mcp_server_path=""

    # First check global installation
    if [ -f "/usr/lib/node_modules/claude-flow/src/mcp/mcp-server.js" ]; then
        mcp_server_path="/usr/lib/node_modules/claude-flow/src/mcp/mcp-server.js"
        log_info "Found global MCP server at: $mcp_server_path"
    else
        # Fallback to npx cache
        mcp_server_path=$(find /home/ubuntu/.npm/_npx -name "mcp-server.js" -path "*/claude-flow/src/mcp/*" 2>/dev/null | head -1)
        if [ -n "$mcp_server_path" ]; then
            log_info "Found cached MCP server at: $mcp_server_path"
        fi
    fi

    if [ -z "$mcp_server_path" ]; then
        log_warning "MCP server not found after installation attempt, skipping patches"
        return 1
    fi

    log_info "Patching MCP server at: $mcp_server_path"

    if dry_run_log "Would patch MCP server at $mcp_server_path"; then return 0; fi

    # Patch 1: Fix hardcoded version
    if grep -q "this.version = '2.0.0-alpha.59'" "$mcp_server_path"; then
        log_info "Patching hardcoded version..."
        sed -i.bak "s|this.version = '2.0.0-alpha.59'|// PATCHED: Dynamic version from package.json\n    try {\n      this.version = require('../../package.json').version;\n    } catch (e) {\n      this.version = '2.0.0-alpha.101'; // Fallback\n    }|" "$mcp_server_path"
        log_success "Patched MCP server version"
    else
        log_info "Version patch already applied or not needed"
    fi

    # Patch 2: Fix method routing to support direct tool calls
    if ! grep -q "PATCHED: Check if method is a direct tool call" "$mcp_server_path"; then
        log_info "Patching method routing for direct tool calls..."

        # Create a temporary file with the patch
        cat > /tmp/mcp_patch.txt << 'PATCH_EOF'
        default:
          // PATCHED: Check if method is a direct tool call
          if (this.tools[method]) {
            console.error(
              `[${new Date().toISOString()}] INFO [claude-flow-mcp] Direct tool call: ${method}`
            );
            // Route direct tool calls to handleToolCall
            return this.handleToolCall(id, { name: method, arguments: params });
          }
          return this.createErrorResponse(id, -32601, 'Method not found');
PATCH_EOF

        # Apply the patch by replacing the default case in handleMessage
        awk '
        /default:.*Method not found/ {
            while ((getline line < "/tmp/mcp_patch.txt") > 0) {
                print line
            }
            close("/tmp/mcp_patch.txt")
            # Skip the original line
            next
        }
        { print }
        ' "$mcp_server_path" > "${mcp_server_path}.patched"

        if [ -f "${mcp_server_path}.patched" ]; then
            mv "${mcp_server_path}.patched" "$mcp_server_path"
            log_success "Patched MCP server method routing"
        else
            log_warning "Failed to apply method routing patch"
        fi

        rm -f /tmp/mcp_patch.txt
    else
        log_info "Method routing patch already applied"
    fi

    # Patch 3: Fix agent tracking - remove mock data fallback
    if grep -q "// Fallback mock response" "$mcp_server_path"; then
        log_info "Patching agent_list to remove mock data fallback..."

        # Create a backup
        cp "$mcp_server_path" "${mcp_server_path}.bak.$(date +%Y%m%d_%H%M%S)"

        # Use sed to remove the mock data section and replace with empty list
        sed -i '/\/\/ Fallback mock response/,/count: 3,/{
            /\/\/ Fallback mock response/i\        // PATCHED: Return empty list instead of mock data\
        console.error(\
          `[${new Date().toISOString()}] WARN [claude-flow-mcp] No real agents found, returning empty list`\
        );
            /\/\/ Fallback mock response/,/count: 3,/d
        }' "$mcp_server_path"

        # Replace the mock return with empty list return
        sed -i "s|swarmId: args.swarmId || 'mock-swarm',|swarmId: args.swarmId || (await this.getActiveSwarmId()) || 'default',|" "$mcp_server_path"
        sed -i "/{ id: 'agent-3', name: 'coder-1'/,/count: 3,/{
            s|agents: \[.*\],|agents: [],|
            s|count: 3,|count: 0,|
        }" "$mcp_server_path"

        log_success "Patched agent_list to remove mock data"
    else
        log_info "Agent list patch already applied or not needed"
    fi

    # Patch 4: Fix agent_spawn to properly track agents with swarmId
    if ! grep -q "PATCHED: Ensure swarmId consistency" "$mcp_server_path"; then
        log_info "Patching agent_spawn for proper swarm tracking..."

        # Add swarmId consistency fix
        sed -i "/case 'agent_spawn':/,/return {/ {
            /const agentId = /a\        // PATCHED: Ensure swarmId consistency\n        const activeSwarmId = args.swarmId || (await this.getActiveSwarmId());
            s/swarmId: args.swarmId || (await this.getActiveSwarmId()),/swarmId: activeSwarmId,/
            /if (global.agentTracker)/,/});/ {
                s/global.agentTracker.trackAgent(agentId, {/global.agentTracker.trackAgent(agentId, {\n            swarmId: activeSwarmId,/
                /});/a\          console.error(\n            \`[\${new Date().toISOString()}] INFO [claude-flow-mcp] Agent tracked: \${agentId} in swarm: \${activeSwarmId}\`,\n          );
            }
        }" "$mcp_server_path"

        log_success "Patched agent_spawn for proper tracking"
    else
        log_info "Agent spawn patch already applied"
    fi

    # Patch 5: Enhanced agent tracker initialization
    if ! grep -q "Agent tracker verified and ready" "$mcp_server_path"; then
        log_info "Patching agent tracker initialization..."

        # Add verification after tracker loading
        sed -i "/\/\/ Initialize agent tracker/,/});/ {
            /});/a\\\n// PATCHED: Verify agent tracker is available\nif (global.agentTracker) {\n  console.error(\`[\${new Date().toISOString()}] INFO [claude-flow-mcp] Agent tracker verified and ready\`);\n} else {\n  console.error(\`[\${new Date().toISOString()}] ERROR [claude-flow-mcp] Agent tracker NOT available - agent tracking will not work!\`);\n}
        }" "$mcp_server_path"

        log_success "Patched agent tracker initialization"
    else
        log_info "Agent tracker init patch already applied"
    fi

    # Restart MCP TCP server to apply patches
    if command -v supervisorctl >/dev/null 2>&1; then
        log_info "Restarting MCP TCP server to apply patches..."
        supervisorctl -c /etc/supervisor/conf.d/supervisord.conf restart mcp-tcp-server 2>/dev/null || {
            # Try killing the process directly if supervisorctl fails
            local mcp_pid=$(pgrep -f "mcp-tcp-server.js" | head -1)
            if [ -n "$mcp_pid" ]; then
                kill -HUP "$mcp_pid" 2>/dev/null && log_success "Sent reload signal to MCP server (PID: $mcp_pid)"
            fi
        }
    fi
}

# Function to patch MCP TCP server for persistence
patch_mcp_tcp_server() {
    log_info "🔧 Patching MCP TCP server for persistent connections..."

    local tcp_server_path="/app/core-assets/scripts/mcp-tcp-server.js"

    if [ ! -f "$tcp_server_path" ]; then
        log_warning "MCP TCP server not found at $tcp_server_path"
        return 1
    fi

    # Check if already patched
    if grep -q "PersistentMCPServer" "$tcp_server_path"; then
        log_info "MCP TCP server already patched for persistence"
        return 0
    fi

    log_info "Creating persistent MCP TCP server..."

    if dry_run_log "Would replace MCP TCP server with persistent version"; then return 0; fi

    # Backup original
    cp "$tcp_server_path" "${tcp_server_path}.original" 2>/dev/null || true

    # Create the persistent server inline (avoiding heredoc issues)
    echo '#!/usr/bin/env node' > "$tcp_server_path"
    echo '' >> "$tcp_server_path"
    echo '// Persistent MCP TCP Server - Fixes agent tracking' >> "$tcp_server_path"
    echo '// Maintains single MCP instance across all connections' >> "$tcp_server_path"
    echo '' >> "$tcp_server_path"

    # Download or copy the persistent version
    if [ -f "/workspace/ext/mcp-tcp-persistent.js" ]; then
        # Use local version if available
        cp /workspace/ext/mcp-tcp-persistent.js "$tcp_server_path"
    else
        # Create minimal persistent version inline
        cat >> "$tcp_server_path" << 'PERSISTENT_SERVER'
const { spawn } = require('child_process');
const net = require('net');
const readline = require('readline');

const TCP_PORT = process.env.MCP_TCP_PORT || 9500;
const LOG_LEVEL = process.env.MCP_LOG_LEVEL || 'info';

class PersistentMCPServer {
  constructor() {
    this.mcpProcess = null;
    this.mcpInterface = null;
    this.clients = new Map();
    this.initialized = false;
    this.initPromise = null;
  }

  log(level, message, ...args) {
    const levels = { debug: 0, info: 1, warn: 2, error: 3 };
    if (levels[level] >= levels[LOG_LEVEL]) {
      console.log(`[PMCP-${level.toUpperCase()}] ${new Date().toISOString()} ${message}`, ...args);
    }
  }

  async startMCPProcess() {
    if (this.mcpProcess) return;

    this.log('info', 'Starting persistent MCP process...');
    this.mcpProcess = spawn('npx', ['claude-flow@alpha', 'mcp', 'start', '--stdio'], {
      stdio: ['pipe', 'pipe', 'pipe'],
      cwd: '/workspace',
      env: { ...process.env, CLAUDE_FLOW_DIRECT_MODE: 'true' }
    });

    this.mcpInterface = readline.createInterface({
      input: this.mcpProcess.stdout,
      crlfDelay: Infinity
    });

    this.mcpInterface.on('line', (line) => this.handleMCPOutput(line));
    this.mcpProcess.stderr.on('data', (data) => this.log('debug', `MCP: ${data}`));
    this.mcpProcess.on('close', (code) => {
      this.log('error', `MCP exited: ${code}`);
      this.mcpProcess = null;
      this.initialized = false;
      setTimeout(() => this.startMCPProcess(), 5000);
    });

    await this.initializeMCP();
  }

  async initializeMCP() {
    if (this.initialized) return;
    const initRequest = {
      jsonrpc: "2.0",
      id: "init-" + Date.now(),
      method: "initialize",
      params: {
        protocolVersion: "2024-11-05",
        capabilities: { tools: { listChanged: true }},
        clientInfo: { name: "tcp-wrapper", version: "1.0.0" }
      }
    };
    return new Promise((resolve) => {
      this.initPromise = { resolve, id: initRequest.id };
      this.mcpProcess.stdin.write(JSON.stringify(initRequest) + '\n');
    });
  }

  handleMCPOutput(line) {
    if (!line.startsWith('{')) return;
    try {
      const msg = JSON.parse(line);
      if (this.initPromise && msg.id === this.initPromise.id) {
        this.initialized = true;
        this.log('info', 'MCP initialized');
        this.initPromise.resolve();
        this.initPromise = null;
        return;
      }
      if (!msg.id) {
        this.broadcastToClients(line);
        return;
      }
      const clientId = this.findClientByRequestId(msg.id);
      if (clientId) {
        const client = this.clients.get(clientId);
        if (client && client.socket) {
          client.socket.write(line + '\n');
        }
      }
    } catch (err) {
      this.log('error', `Parse error: ${err.message}`);
    }
  }

  findClientByRequestId(requestId) {
    for (const [clientId, client] of this.clients) {
      if (client.pendingRequests && client.pendingRequests.has(requestId)) {
        client.pendingRequests.delete(requestId);
        return clientId;
      }
    }
    return null;
  }

  broadcastToClients(message) {
    for (const [clientId, client] of this.clients) {
      if (client.socket && !client.socket.destroyed) {
        client.socket.write(message + '\n');
      }
    }
  }

  async handleClient(socket) {
    const clientId = `${socket.remoteAddress}:${socket.remotePort}-${Date.now()}`;
    this.log('info', `Client connected: ${clientId}`);

    if (!this.initialized) {
      let waitCount = 0;
      while (!this.initialized && waitCount < 20) {
        await new Promise(resolve => setTimeout(resolve, 100));
        waitCount++;
      }
      if (!this.initialized) {
        socket.write('{"error":"MCP not ready"}\n');
        socket.end();
        return;
      }
    }

    this.clients.set(clientId, {
      socket,
      pendingRequests: new Set(),
      buffer: ''
    });

    socket.on('data', (data) => {
      const client = this.clients.get(clientId);
      if (!client) return;
      client.buffer += data.toString();
      const lines = client.buffer.split('\n');
      client.buffer = lines.pop() || '';
      for (const line of lines) {
        if (line.trim()) this.handleClientRequest(clientId, line);
      }
    });

    socket.on('close', () => {
      this.log('info', `Client disconnected: ${clientId}`);
      this.clients.delete(clientId);
    });

    socket.on('error', (err) => {
      this.log('error', `Client error: ${err.message}`);
      this.clients.delete(clientId);
    });
  }

  handleClientRequest(clientId, requestStr) {
    try {
      const request = JSON.parse(requestStr);
      const client = this.clients.get(clientId);
      if (!client) return;

      if (request.method === 'initialize') {
        client.socket.write(JSON.stringify({
          jsonrpc: "2.0",
          id: request.id,
          result: {
            protocolVersion: "2024-11-05",
            serverInfo: { name: "claude-flow", version: "2.0.0-alpha.101" }
          }
        }) + '\n');
        return;
      }

      if (request.id) {
        client.pendingRequests.add(request.id);
      }
      this.mcpProcess.stdin.write(requestStr + '\n');
      this.log('debug', `Forwarded: ${request.id}`);
    } catch (err) {
      this.log('error', `Invalid request: ${err.message}`);
    }
  }

  async start() {
    await this.startMCPProcess();
    const server = net.createServer((socket) => this.handleClient(socket));
    server.listen(TCP_PORT, '0.0.0.0', () => {
      this.log('info', `Persistent MCP TCP server on port ${TCP_PORT}`);
    });
    server.on('error', (err) => {
      this.log('error', `Server error: ${err.message}`);
      if (err.code === 'EADDRINUSE') process.exit(1);
    });
  }
}

const server = new PersistentMCPServer();
server.start().catch(err => {
  console.error('Failed to start:', err);
  process.exit(1);
});

process.on('SIGINT', () => {
  if (server.mcpProcess) server.mcpProcess.kill();
  process.exit(0);
});
PERSISTENT_SERVER
    fi

    chmod +x "$tcp_server_path"
    log_success "Replaced MCP TCP server with persistent version"
}

if [ "$DRY_RUN" = false ]; then
    patch_mcp_server
    patch_mcp_tcp_server
else
    dry_run_log "Would patch MCP server"
    dry_run_log "Would patch MCP TCP server"
fi

# --- Final Summary ---
show_setup_summary() {
    # Create the completion marker file to hide the welcome message
    if [ "$DRY_RUN" = false ]; then
        touch /workspace/.setup_completed
        chown dev:dev /workspace/.setup_completed
    fi

    echo ""
    echo "=== ✅ Enhanced Setup Complete ==="
    echo ""

    if [ "$DRY_RUN" = true ]; then
        echo "🔍 DRY RUN COMPLETE - No changes were made."
        return 0
    fi

    echo "📋 Setup Summary:"
    echo "  - Merged MCP configuration into .mcp.json"
    echo "  - Configured toolchain PATHs in /etc/profile.d/"
    echo "  - Added supervisorctl-based aliases to .bashrc"
    echo "  - Appended environment context to CLAUDE.md"
    echo ""

    echo "🛠️  Key Commands:"
    echo "  - mcp-tcp-status, mcp-ws-status"
    echo "  - mcp-test-health, validate-toolchains"
    echo ""

    echo "💡 Development Context:"
    echo "  - Your project root is in: ext/"
    echo "  - Use internal tools like 'cargo check' to validate your work."
    echo "  - Claude cannot build or see external Docker services."
    echo ""
}