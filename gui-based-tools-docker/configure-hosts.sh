#!/bin/bash
# Configure hostname resolution for MCP services

echo "Configuring hostname resolution for MCP services..."

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then 
    echo "This script needs to modify /etc/hosts. Please run with sudo or as root."
    echo "Usage: sudo $0"
    exit 1
fi

# Function to add or update hosts entry
update_hosts_entry() {
    local ip=$1
    local hostname=$2
    local hosts_file="/etc/hosts"
    
    # Remove existing entry if present
    if [ "$EUID" -eq 0 ]; then
        sed -i.bak "/ $hostname$/d" "$hosts_file"
        echo "$ip $hostname" >> "$hosts_file"
    else
        sudo sed -i.bak "/ $hostname$/d" "$hosts_file"
        echo "$ip $hostname" | sudo tee -a "$hosts_file" > /dev/null
    fi
}

# Default IPs - these should match your Docker network
BLENDER_IP="${BLENDER_IP:-172.18.0.9}"
BLENDER_HOSTNAME="blender_desktop"

# Add entries
echo "Adding hostname entries..."
update_hosts_entry "$BLENDER_IP" "$BLENDER_HOSTNAME"

echo "Updated /etc/hosts with:"
grep "$BLENDER_HOSTNAME" /etc/hosts

echo
echo "Hostname resolution configured successfully!"
echo "You can now use 'blender_desktop' instead of IP addresses."
echo
echo "To test:"
echo "  ping blender_desktop"
echo "  nc -zv blender_desktop 9876"