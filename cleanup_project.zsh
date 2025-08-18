#!/bin/zsh

echo "🚀 Starting project cleanup..."

# List of files and directories to be removed with reasons
declare -A files_to_remove=(
  ["gui-based-tools-docker/verify_emissive.py"]="Developer verification script, not needed for runtime."
  ["gui-based-tools-docker/tessellating-pbr-generator/preview_usage_example.py"]="Example code, should be in documentation, not the codebase."
  ["gui-based-tools-docker/tessellating-pbr-generator/package.json"]="Unused Node.js package file in a Python project."
  ["gui-based-tools-docker/test-mcp-connectivity.sh"]="Redundant functionality covered by mcp-helper.sh and TROUBLESHOOTING.md."
  ["test-tcp-connection.md"]="Developer-level debugging info. Core details are in README.md, making this file redundant."
  ["gui-based-tools-docker/configure-hosts.sh"]="Encourages anti-pattern of modifying /etc/hosts; Docker networking makes this unnecessary."
  ["gui-based-tools-docker/setup-mcp-env.sh"]="Redundant script; environment variables are correctly set by docker-compose.yml."
  ["gui-based-tools-docker/README.md"]="Confusing duplicate; information should be consolidated in the root README.md."
  ["gui-based-tools-docker/TROUBLESHOOTING.md"]="Confusing duplicate; information should be consolidated in the root TROUBLESHOOTING.md."
)

# Remove specified files
for file reason in ${(kv)files_to_remove}; do
  if [[ -f "$file" ]]; then
    echo "🔥 Removing: $file"
    echo "   Reason: $reason"
    rm "$file"
    echo "   ...Removed."
  else
    echo "⚠️  Skipping (not found): $file"
  fi
done

# Move the TCP server script from 'patches' to a more logical location
PATCH_DIR="core-assets/patches"
SCRIPT_DIR="core-assets/scripts"
TCP_SERVER_SCRIPT="mcp-tcp-server.js"

if [[ -f "$PATCH_DIR/$TCP_SERVER_SCRIPT" ]]; then
  echo "🚚 Moving TCP server script from '$PATCH_DIR' to '$SCRIPT_DIR'..."
  if [[ ! -d "$SCRIPT_DIR" ]]; then
    mkdir -p "$SCRIPT_DIR"
  fi
  mv "$PATCH_DIR/$TCP_SERVER_SCRIPT" "$SCRIPT_DIR/"
  
  # Update the setup script to reflect the new location
  SETUP_SCRIPT="setup-workspace.sh"
  OLD_PATH="$PATCH_DIR/$TCP_SERVER_SCRIPT"
  NEW_PATH_IN_CONTAINER="/app/scripts/$TCP_SERVER_SCRIPT" # Path inside the container
  # Note: The setup script copies from /app/core-assets/patches, this needs to be changed.
  # This is a simple string replacement; a more robust solution would parse the script.
  echo "   Updating setup script '$SETUP_SCRIPT'..."
  sed -i.bak "s|/app/core-assets/patches/mcp-tcp-server.js|/app/core-assets/scripts/mcp-tcp-server.js|g" "$SETUP_SCRIPT"
  sed -i.bak "s|/app/patches/mcp-tcp-server.js|/app/scripts/mcp-tcp-server.js|g" "$SETUP_SCRIPT"
  rm "${SETUP_SCRIPT}.bak"
  
  echo "   ...Move complete."
else
  echo "✅ TCP server script already in correct location or not found in patches."
fi


echo ""
echo "✅ Project cleanup finished."
echo "⚠️  Please review and commit the changes."