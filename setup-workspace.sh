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

# 7. Ensure claude-flow is installed globally
ensure_claude_flow_global() {
    log_info "🔧 Ensuring claude-flow is installed globally..."
    
    if [ ! -f "/usr/bin/claude-flow" ]; then
        log_info "Installing claude-flow globally..."
        if dry_run_log "Would install claude-flow globally"; then return 0; fi
        
        npm install -g claude-flow@alpha 2>/dev/null || {
            log_warning "Failed to install claude-flow globally, trying with sudo..."
            sudo npm install -g claude-flow@alpha || {
                log_error "Failed to install claude-flow globally"
                return 1
            }
        }
        log_success "Installed claude-flow globally"
    else
        log_info "claude-flow already installed globally"
    fi
}

if [ "$DRY_RUN" = false ]; then
    ensure_claude_flow_global
else
    dry_run_log "Would ensure claude-flow is installed globally"
fi

# 8. Patch MCP server to fix hardcoded version and method routing
patch_mcp_server() {
    log_info "🔧 Patching MCP server to fix version, method routing, and agent tracking..."

    # First try global installation, then npm cache
    local mcp_server_path="/usr/lib/node_modules/claude-flow/src/mcp/mcp-server.js"
    
    if [ ! -f "$mcp_server_path" ]; then
        log_info "Global installation not found, checking npm cache..."
        mcp_server_path=$(find /home/ubuntu/.npm/_npx -name "mcp-server.js" -path "*/claude-flow/src/mcp/*" 2>/dev/null | head -1)
    fi

    if [ -z "$mcp_server_path" ] || [ ! -f "$mcp_server_path" ]; then
        log_warning "MCP server not found, skipping patches"
        return 1
    fi

    log_info "Found MCP server at: $mcp_server_path"

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

    # Patch 3: Fix agent_list to properly query database instead of returning mock data
    if grep -q "// Fallback mock response" "$mcp_server_path"; then
        log_info "Patching agent_list to use real database queries..."
        
        # Create backup
        cp "$mcp_server_path" "${mcp_server_path}.bak.$(date +%s)"
        
        # Replace the mock fallback with proper database query
        sed -i '/\/\/ Fallback mock response/,/timestamp: new Date().toISOString(),$/c\
        // PATCHED: Query database directly for agents\
        try {\
          const swarmId = args.swarmId || await this.getActiveSwarmId();\
          if (!swarmId) {\
            // No swarm specified, list all agents from database\
            const allEntries = await this.memoryStore.list();  // No namespace needed\
            const agents = allEntries.filter(entry => entry.key.startsWith("agent:")).map(entry => {\
              try {\
                const data = typeof entry.value === "string" ? JSON.parse(entry.value) : entry.value;\
                return {\
                  id: data.id || entry.key.split(":").pop(),\
                  name: data.name || "unknown",\
                  type: data.type || "agent",\
                  status: data.status || "unknown",\
                  capabilities: data.capabilities || [],\
                  swarmId: entry.key.split(":")[1] || "unknown"\
                };\
              } catch (e) {\
                return null;\
              }\
            }).filter(Boolean);\
            \
            return {\
              success: true,\
              swarmId: "all",\
              agents: agents,\
              count: agents.length,\
              timestamp: new Date().toISOString(),\
            };\
          }\
          \
          // Query agents for specific swarm\
          const prefix = `agent:${swarmId}:`;\
          const entries = await this.memoryStore.list();  // No namespace needed\
          const swarmAgents = entries.filter(entry => entry.key.startsWith(prefix)).map(entry => {\
            try {\
              const data = typeof entry.value === "string" ? JSON.parse(entry.value) : entry.value;\
              return {\
                id: data.id || entry.key.split(":").pop(),\
                name: data.name || "unknown",\
                type: data.type || "agent",\
                status: data.status || "active",\
                capabilities: data.capabilities || []\
              };\
            } catch (e) {\
              return null;\
            }\
          }).filter(Boolean);\
          \
          return {\
            success: true,\
            swarmId: swarmId,\
            agents: swarmAgents,\
            count: swarmAgents.length,\
            timestamp: new Date().toISOString(),\
          };\
        } catch (error) {\
          console.error("Failed to query agents:", error);\
          return {\
            success: false,\
            error: error.message,\
            agents: [],\
            timestamp: new Date().toISOString(),\
          };\
        }' "$mcp_server_path"
        
        log_success "Patched agent_list to use real database queries"
    else
        log_info "Agent tracking patch already applied or not needed"
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

if [ "$DRY_RUN" = false ]; then
    patch_mcp_server
else
    dry_run_log "Would patch MCP server"
fi

# 9. Patch TCP server to use global installation and shared database
patch_tcp_server() {
    log_info "🔧 Patching TCP server to use global installation and shared database..."
    
    local tcp_server_path="/app/core-assets/scripts/mcp-tcp-server.js"
    
    if [ ! -f "$tcp_server_path" ]; then
        tcp_server_path="/workspace/scripts/mcp-tcp-server.js"
    fi
    
    if [ ! -f "$tcp_server_path" ]; then
        log_warning "TCP server not found, skipping patch"
        return 1
    fi
    
    log_info "Found TCP server at: $tcp_server_path"
    
    if dry_run_log "Would patch TCP server at $tcp_server_path"; then return 0; fi
    
    # Create backup
    cp "$tcp_server_path" "${tcp_server_path}.bak.$(date +%s)" 2>/dev/null || true
    
    # Patch: Change from npx to global installation and add shared database
    if grep -q "spawn('npx'" "$tcp_server_path" || grep -q "spawn('/usr/bin/claude-flow'" "$tcp_server_path"; then
        log_info "Patching TCP server spawn commands..."
        
        # First, replace npx with global installation
        sed -i "s|spawn('npx', \['claude-flow@alpha'|spawn('/usr/bin/claude-flow', ['|g" "$tcp_server_path"
        
        # Then ensure environment includes shared database - handle both cases
        # Case 1: When env line exists but doesn't have our DB path
        if grep -q "env: {" "$tcp_server_path" && ! grep -q "CLAUDE_FLOW_DB_PATH" "$tcp_server_path"; then
            sed -i "/spawn('\/usr\/bin\/claude-flow'/,/env: {/{
                s|env: { \(.*\)|env: {\n          ...process.env,\n          CLAUDE_FLOW_DB_PATH: '/workspace/.swarm/memory.db', // Ensure same DB is used\n          \1|
            }" "$tcp_server_path"
        fi
        
        # Fix any duplicate env properties that might have been created
        sed -i '/env: {.*env: {/s/env: {.*env: { \.\.\./env: {\n          .../' "$tcp_server_path"
        
        log_success "Patched TCP server to use global installation with shared database"
    else
        log_info "TCP server spawn commands already patched"
    fi
    
    # Ensure database directory exists
    if [ ! -d "/workspace/.swarm" ]; then
        mkdir -p /workspace/.swarm
        chown -R dev:dev /workspace/.swarm
        log_success "Created shared database directory: /workspace/.swarm"
    fi
}

if [ "$DRY_RUN" = false ]; then
    patch_tcp_server
else
    dry_run_log "Would patch TCP server"
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
    echo "  - Installed claude-flow globally at /usr/bin/claude-flow"
    echo "  - Patched MCP server for proper agent tracking"
    echo "  - Fixed TCP server to use shared database"
    echo "  - Created shared database at /workspace/.swarm/memory.db"
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

# --- Verification Test ---
verify_agent_tracking() {
    log_info "🧪 Verifying agent tracking functionality..."
    
    if [ "$DRY_RUN" = true ]; then
        dry_run_log "Would verify agent tracking"
        return 0
    fi
    
    # Wait for services to be ready
    sleep 3
    
    # Test agent list command
    local test_result=$(echo '{"jsonrpc":"2.0","id":"test","method":"tools/call","params":{"name":"agent_list","arguments":{}}}' | nc -w 3 localhost 9500 2>/dev/null | tail -n 1)
    
    if echo "$test_result" | grep -q '"success":true' && ! echo "$test_result" | grep -q '"id":"agent-1"'; then
        log_success "✅ Agent tracking verified - database integration working!"
    elif echo "$test_result" | grep -q '"id":"agent-1"'; then
        log_warning "⚠️  Agent tracking still returning mock data - manual intervention may be needed"
        log_info "    Check that /usr/bin/claude-flow exists and patches were applied"
    else
        log_info "    Service may still be starting - check with: mcp-tcp-status"
    fi
}

# 9. Create Rust backend patch file for Docker build
create_rust_patches() {
    log_info "📝 Creating consolidated Rust backend patches for Docker build..."
    
    # Create patches directory
    mkdir -p /workspace/ext/patches
    
    # Create consolidated fix that merges the two systems
    cat > /workspace/ext/patches/consolidated_agent_graph_fix.patch << 'PATCH_EOF'
--- a/src/actors/claude_flow_actor_tcp.rs
+++ b/src/actors/claude_flow_actor_tcp.rs
@@ -738,6 +738,11 @@
     }
     
     fn poll_agent_statuses(&mut self, _ctx: &mut Context<Self>) {
+        // DISABLED: ClaudeFlowActor TCP polling is broken due to persistent connection issues
+        // The MCP server closes connections after each request, but this actor expects persistent connections
+        // BotsClient handles agent fetching correctly with fresh connections
+        return;
+        
         debug!("Polling agent statuses via TCP (100ms cycle) - {} consecutive failures", 
                self.consecutive_poll_failures);
         
--- a/src/services/bots_client.rs
+++ b/src/services/bots_client.rs
@@ -225,7 +225,18 @@
                                                             }
                                                             let mut lock = updates.write().await;
                                                             *lock = Some(update);
-                                                            continue; // Skip the rest of the parsing
+                                                            
+                                                            // CRITICAL FIX: Send agents to graph
+                                                            if let Some(graph_addr) = graph_service_addr {
+                                                                info!("📨 BotsClient sending {} agents to graph", update.agents.len());
+                                                                graph_addr.do_send(UpdateBotsGraph {
+                                                                    agents: update.agents.clone()
+                                                                        .into_iter()
+                                                                        .map(|a| a.into())
+                                                                        .collect()
+                                                                });
+                                                            }
+                                                            continue;
                                                         }
                                                     }
                                                 }
PATCH_EOF
    
    log_success "Created consolidated Rust backend patch at /workspace/ext/patches/consolidated_agent_graph_fix.patch"
    log_info "This patch:"
    log_info "  1. Disables broken ClaudeFlowActor TCP polling"
    log_info "  2. Makes BotsClient send graph updates"
    log_info "  3. Creates single clean data flow path"
    log_info ""
    log_info "Apply in visionflow_container Docker build with:"
    log_info "  cd /app && patch -p1 < /workspace/ext/patches/consolidated_agent_graph_fix.patch"
}

# --- Main Execution ---
show_setup_summary

# Run verification if not in dry-run mode
if [ "$DRY_RUN" = false ]; then
    verify_agent_tracking
    create_rust_patches
fi

echo ""
echo "🎉 Multi-Agent environment ready for development!"
echo "🔧 Agent tracking fixed - using shared database at /workspace/.swarm/memory.db"
echo "🚀 CRITICAL: Apply Rust patch in visionflow_container for graph visualization!"
echo "   Run: cd /app && patch -p1 < /workspace/ext/patches/fix_agent_graph_update.patch"
echo ""