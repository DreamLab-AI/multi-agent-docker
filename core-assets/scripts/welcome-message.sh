#!/bin/sh
# This script is sourced by /etc/bash.bashrc to display a one-time welcome message.

if [ ! -f "/workspace/.setup_completed" ]; then
    echo ""
    echo "--- 🚀 Welcome to the Multi-Agent Docker Environment ---"
    echo ""
    echo "To complete your one-time setup, please run the following commands in order:"
    echo ""
    echo "0. claude --dangerously-skip-permissions"
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
    echo "This message will disappear after you run the setup script."
    echo "--------------------------------------------------------"
    echo ""
fi