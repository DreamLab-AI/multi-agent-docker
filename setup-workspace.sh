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

# --- 🚀 Welcome & Setup Instructions ---
if [ -z "$SETUP_COMPLETED" ]; then
    echo ""
    echo "--- 🚀 Welcome to the Multi-Agent Docker Environment ---"
    echo ""
    echo "To complete your one-time setup, please run the following commands in order:"
    echo ""
    echo "1. Authenticate with Claude (only if this is your first time):"
    echo "   claude auth"
    echo ""
    echo "2. Initialize the Claude Flow workspace:"
    echo "   npx claude-flow@alpha init --force"
    echo ""
    echo "3. Run the environment enhancement script:"
    echo "   /app/setup-workspace.sh"
    echo ""
    echo "4. Reload your shell to activate all aliases and settings:"
    echo "   source ~/.bashrc"
    echo ""
    echo "You can set 'export SETUP_COMPLETED=true' in this file to hide this message."
    echo "--------------------------------------------------------"
    echo ""
fi

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
- **Project Root**: Your project is mounted at `/workspace/ext/`.
- **Execution Environment**: Claude operates within this Docker container. It cannot build external Docker images or see services running on your host machine.
- **Available Toolchains**: You can validate your code using tools inside this container, such as `cargo check`, `npm test`, or `python -m py_compile`.

### Quick Commands
```bash
# Check code without a full build
cargo check         # For Rust projects in /workspace/ext
npm run test        # For Node.js projects in /workspace/ext

# Manage and test MCP services
mcp-tcp-status
mcp-test-health
validate-toolchains
```
EOF
    log_success "Appended service and context info to CLAUDE.md"
}

update_claude_md

# --- Final Summary ---
show_setup_summary() {
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
    echo "  - Your project root is in: /workspace/ext/"
    echo "  - Use internal tools like 'cargo check' to validate your work."
    echo "  - Claude cannot build or see external Docker services."
    echo ""
}

show_setup_summary