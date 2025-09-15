#!/bin/bash
# Enhanced setup script for the Multi-Agent Docker Environment
#
# This script is now primarily for user feedback and future runtime tasks.
# The core setup has been moved into the Dockerfile for a streamlined
# and idempotent build process.

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

# --- Main Execution ---
echo "🚀 Multi-Agent workspace is pre-initialized."
[ "$DRY_RUN" = true ] && echo "🔍 DRY RUN MODE - No changes will be made"

# The core setup logic has been moved to the Dockerfile.
# This script can be extended with runtime-specific tasks if needed.

# --- Final Summary ---
show_setup_summary() {
    # Create the completion marker file to hide the welcome message
    if [ "$DRY_RUN" = false ]; then
        touch /workspace/.setup_completed
        chown dev:dev /workspace/.setup_completed
    fi

    echo ""
    echo "=== ✅ Workspace Initialized ==="
    echo ""

    if [ "$DRY_RUN" = true ]; then
        echo "🔍 DRY RUN COMPLETE - No changes were made."
        return 0
    fi

    echo "📋 Environment Summary:"
    echo "  - Core assets and MCP configuration are pre-installed."
    echo "  - Toolchain PATHs are configured in /etc/profile.d/"
    echo "  - Supervisorctl-based aliases are available in your shell."
    echo ""

    echo "🛠️  Key Commands:"
    echo "  - mcp-tcp-status, mcp-ws-status"
    echo "  - mcp-test-health, validate-toolchains"
    echo ""

    echo "💡 Next Steps:"
    echo "  - If you haven't already, log in to Claude:"
    echo "    claude login"
    echo "  - Your project root is in: ext/"
    echo ""
}

show_setup_summary