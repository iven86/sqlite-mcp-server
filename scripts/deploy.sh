#!/bin/bash
# SQLite MCP Server - Production Deployment Script

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "SQLite MCP Server - Production Deployment"
echo "========================================="

# Configuration
SERVICE_USER="${MCP_USER:-mcp}"
SERVICE_NAME="sqlite-mcp-server"
INSTALL_DIR="/opt/sqlite-mcp-server"
CONFIG_DIR="/etc/sqlite-mcp-server"
LOG_DIR="/var/log/sqlite-mcp-server"
SYSTEMD_SERVICE="/etc/systemd/system/${SERVICE_NAME}.service"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root for system-wide installation"
   echo "For local installation, use ./start_server.sh instead"
   exit 1
fi

echo "Creating service user..."
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd --system --home-dir "$INSTALL_DIR" --shell /bin/false "$SERVICE_USER"
    echo "Created user: $SERVICE_USER"
else
    echo "User $SERVICE_USER already exists"
fi

echo "Creating directories..."
mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$LOG_DIR"
chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR" "$LOG_DIR"

echo "Installing server files..."
# Copy main entry point and src directory for the modular structure
cp main.py "$INSTALL_DIR/"
cp -r src/ "$INSTALL_DIR/"
cp README.md "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/main.py"
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

echo "Creating configuration file..."
cat > "$CONFIG_DIR/config.env" << EOF
# SQLite MCP Server Configuration
MCP_HOST=localhost
MCP_PORT=9999
MCP_LOG_LEVEL=INFO
MCP_LOG_DIR=$LOG_DIR
MCP_MAX_CONNECTIONS=20
MCP_MAX_QUERY_TIME=60
MCP_MAX_RESULT_ROWS=10000
EOF

echo "Creating systemd service..."
cat > "$SYSTEMD_SERVICE" << EOF
[Unit]
Description=SQLite MCP Server
After=network.target

[Service]
Type=exec
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$CONFIG_DIR/config.env
ExecStart=/usr/bin/python3 $INSTALL_DIR/main.py --host \${MCP_HOST} --port \${MCP_PORT} --log-level \${MCP_LOG_LEVEL} --max-connections \${MCP_MAX_CONNECTIONS} --max-query-time \${MCP_MAX_QUERY_TIME} --max-result-rows \${MCP_MAX_RESULT_ROWS}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=sqlite-mcp-server

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$LOG_DIR

[Install]
WantedBy=multi-user.target
EOF

echo "Enabling and starting service..."
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl start "$SERVICE_NAME"

echo ""
echo "Deployment complete!"
echo "==================="
echo "Service: $SERVICE_NAME"
echo "Status: systemctl status $SERVICE_NAME"
echo "Logs: journalctl -u $SERVICE_NAME -f"
echo "Config: $CONFIG_DIR/config.env"
echo "Install dir: $INSTALL_DIR"
echo ""
echo "Server should be running on: http://localhost:9999"
echo "Health check: curl http://localhost:9999/health"
