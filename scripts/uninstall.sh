#!/bin/bash
# SQLite MCP Server - Complete Uninstall Script

set -e

echo "SQLite MCP Server - Complete Uninstall"
echo "======================================"
echo ""
echo "⚠️  WARNING: This will completely remove the SQLite MCP Server installation"
echo "including all configuration files and logs."
echo ""
read -p "Are you sure you want to continue? (y/N): " confirm

if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled."
    exit 0
fi

echo ""
echo "Starting complete uninstall..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)"
   exit 1
fi

# Function to safely remove service
remove_service() {
    local service_name="$1"
    echo "🗑️  Removing service: $service_name"
    
    if systemctl is-active --quiet "$service_name" 2>/dev/null; then
        echo "   - Stopping service..."
        systemctl stop "$service_name"
    fi
    
    if systemctl is-enabled --quiet "$service_name" 2>/dev/null; then
        echo "   - Disabling service..."
        systemctl disable "$service_name"
    fi
    
    if [[ -f "/etc/systemd/system/$service_name.service" ]]; then
        echo "   - Removing service file..."
        rm -f "/etc/systemd/system/$service_name.service"
    fi
}

# Remove all possible service variants
remove_service "sqlite-mcp-server"
remove_service "sqlite-mcp"
remove_service "mcp-server"

# Reload systemd
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload

# Remove mcp user if it exists
if id "mcp" &>/dev/null; then
    echo "🧹 Removing mcp user..."
    userdel -r mcp 2>/dev/null || true
fi

# Remove system directories
echo "🗂️  Removing system directories..."
rm -rf /opt/sqlite-mcp-server
rm -rf /var/lib/sqlite-mcp-server
rm -rf /var/log/sqlite-mcp-server
rm -rf /etc/sqlite-mcp-server

# Get the actual user (when running with sudo)
ACTUAL_USER="${SUDO_USER:-$USER}"
if [[ "$ACTUAL_USER" != "root" ]]; then
    USER_HOME=$(getent passwd "$ACTUAL_USER" | cut -d: -f6)
    
    echo "🏠 Removing user directories for $ACTUAL_USER..."
    sudo -u "$ACTUAL_USER" rm -rf "$USER_HOME/.local/share/sqlite-mcp-server" 2>/dev/null || true
    sudo -u "$ACTUAL_USER" rm -rf "$USER_HOME/.config/sqlite-mcp-server" 2>/dev/null || true
fi

# Remove any remaining processes
echo "🔍 Checking for remaining processes..."
pkill -f "sqlite.*mcp" 2>/dev/null || true
pkill -f "main.py" 2>/dev/null || true

echo ""
echo "✅ Uninstall completed successfully!"
echo ""
echo "The following items have been removed:"
echo "   - All systemd services (sqlite-mcp-server, sqlite-mcp, mcp-server)"
echo "   - mcp system user and home directory"
echo "   - System directories (/opt, /var/lib, /var/log, /etc)"
echo "   - User directories (~/.local/share, ~/.config)"
echo "   - Running processes"
echo ""
echo "You can now run the deploy script again with your preferred mode:"
echo "   sudo ./scripts/deploy.sh --user-mode"
echo "   sudo ./scripts/deploy.sh --system-mode"
