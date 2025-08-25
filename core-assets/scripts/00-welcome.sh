#!/bin/sh
# /etc/profile.d/00-welcome.sh
#
# This script displays a welcome message and one-time setup instructions
# for the Multi-Agent Docker Environment.

# Check if the setup has been marked as complete to avoid showing this on every login.
# The user can create this file manually after setup.
if [ ! -f "/workspace/.setup_completed" ]; then
    echo ""
    echo "--- 🚀 Welcome to the Multi-Agent Docker Environment ---"
    echo ""
    echo "To complete your one-time setup, please run the following commands in order:"
    echo ""
    echo "1. Initialize the Claude Flow workspace (this may require auth):"
    echo "   npx claude-flow@alpha init --force"
    echo ""
    echo "2. Run the environment enhancement script:"
    echo "   /app/setup-workspace.sh"
    echo ""
    echo "3. Reload your shell to activate all aliases and settings:"
    echo "   source ~/.bashrc"
    echo ""
    echo "After setup, you can hide this message by running: touch /workspace/.setup_completed"
    echo "--------------------------------------------------------"
    echo ""
fi