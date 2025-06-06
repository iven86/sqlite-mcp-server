#!/bin/bash
# SQLite MCP Server - Enhanced Deployment Script

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Display usage information
usage() {
    echo "SQLite MCP Server - Enhanced Deployment Script"
    echo "=============================================="
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Deployment Modes:"
    echo "  --user-mode     Deploy as current user (recommended for development)"
    echo "                  - Runs with your user permissions"
    echo "                  - Can access your home directory and databases"
    echo "                  - Uses ~/.config/sqlite-mcp-server/"
    echo ""
    echo "  --system-mode   Deploy as system service with dedicated user"
    echo "                  - Creates 'mcp' system user"
    echo "                  - Higher security isolation"
    echo "                  - Requires explicit database permissions"
    echo "                  - Uses /opt/sqlite-mcp-server/"
    echo ""
    echo "Options:"
    echo "  --port PORT     Set server port (default: 9999)"
    echo "  --host HOST     Set server host (default: localhost)"
    echo "  --help          Show this help message"
    echo ""
    echo "Prerequisites:"
    echo "  - Python 3.7+ installed"
    echo "  - Install dependencies: pip3 install -r requirements.txt"
    echo ""
    echo "Examples:"
    echo "  pip3 install -r requirements.txt       # Install dependencies first"
    echo "  sudo $0 --user-mode                    # Deploy as current user"
    echo "  sudo $0 --system-mode                  # Deploy as system service"
    echo "  sudo $0 --user-mode --port 8080        # Deploy with custom port"
    echo ""
    exit 1
}

# Parse command line arguments
DEPLOY_MODE=""
SERVER_PORT="9999"
SERVER_HOST="localhost"

while [[ $# -gt 0 ]]; do
    case $1 in
        --user-mode)
            DEPLOY_MODE="user"
            shift
            ;;
        --system-mode)
            DEPLOY_MODE="system"
            shift
            ;;
        --port)
            SERVER_PORT="$2"
            shift 2
            ;;
        --host)
            SERVER_HOST="$2"
            shift 2
            ;;
        --help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Check if deployment mode was specified
if [[ -z "$DEPLOY_MODE" ]]; then
    echo "Error: You must specify a deployment mode!"
    echo ""
    usage
fi

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)"
   echo "For local development without systemd, use: ./scripts/start_server.sh"
   exit 1
fi

# Get the actual user (when running with sudo)
ACTUAL_USER="${SUDO_USER:-$USER}"
if [[ "$ACTUAL_USER" == "root" ]]; then
    echo "Error: Cannot determine the actual user. Don't run as root directly."
    echo "Use: sudo $0 [options]"
    exit 1
fi

echo "SQLite MCP Server - Enhanced Deployment"
echo "======================================="
echo "Mode: $DEPLOY_MODE"
echo "User: $ACTUAL_USER"
echo "Port: $SERVER_PORT"
echo "Host: $SERVER_HOST"
echo ""

# Deployment functions
deploy_user_mode() {
    echo "🔧 Deploying in User Mode..."
    echo "============================="
    
    # Configuration for user mode
    SERVICE_USER="$ACTUAL_USER"
    SERVICE_NAME="sqlite-mcp-server"
    USER_HOME=$(getent passwd "$ACTUAL_USER" | cut -d: -f6)
    INSTALL_DIR="$USER_HOME/.local/share/sqlite-mcp-server"
    CONFIG_DIR="$USER_HOME/.config/sqlite-mcp-server"
    LOG_DIR="$USER_HOME/.local/share/sqlite-mcp-server/logs"
    SYSTEMD_SERVICE="/etc/systemd/system/${SERVICE_NAME}.service"
    
    echo "Creating directories..."
    sudo -u "$ACTUAL_USER" mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$LOG_DIR"
    
    echo "Installing server files..."
    sudo -u "$ACTUAL_USER" cp main.py "$INSTALL_DIR/"
    sudo -u "$ACTUAL_USER" cp -r src/ "$INSTALL_DIR/"
    sudo -u "$ACTUAL_USER" cp README.md "$INSTALL_DIR/"
    sudo -u "$ACTUAL_USER" cp requirements.txt "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/main.py"
    
    echo "Creating configuration file..."
    sudo -u "$ACTUAL_USER" tee "$CONFIG_DIR/config.env" > /dev/null << EOF
# SQLite MCP Server Configuration - User Mode
MCP_HOST=$SERVER_HOST
MCP_PORT=$SERVER_PORT
MCP_LOG_LEVEL=INFO
MCP_LOG_DIR=$LOG_DIR
MCP_MAX_CONNECTIONS=20
MCP_MAX_QUERY_TIME=60
MCP_MAX_RESULT_ROWS=10000
EOF

    echo "Creating systemd service..."
    cat > "$SYSTEMD_SERVICE" << EOF
[Unit]
Description=SQLite MCP Server (User Mode)
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

# Minimal security settings for user mode
NoNewPrivileges=true
PrivateTmp=false
ProtectSystem=false
ProtectHome=false

[Install]
WantedBy=multi-user.target
EOF

    echo "✅ User mode deployment complete!"
    echo "Configuration: $CONFIG_DIR/config.env"
    echo "Installation: $INSTALL_DIR"
    echo "Logs: $LOG_DIR"
}

deploy_system_mode() {
    echo "🔒 Deploying in System Mode..."
    echo "==============================="
    
    # Configuration for system mode
    SERVICE_USER="mcp"
    SERVICE_NAME="sqlite-mcp-server"
    INSTALL_DIR="/opt/sqlite-mcp-server"
    CONFIG_DIR="/etc/sqlite-mcp-server"
    LOG_DIR="/var/log/sqlite-mcp-server"
    DATABASE_DIR="/var/lib/sqlite-mcp-server/databases"
    SYSTEMD_SERVICE="/etc/systemd/system/${SERVICE_NAME}.service"
    
    echo "Creating service user..."
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd --system --home-dir "$INSTALL_DIR" --shell /bin/false "$SERVICE_USER"
        echo "Created user: $SERVICE_USER"
    else
        echo "User $SERVICE_USER already exists"
    fi
    
    echo "Creating directories..."
    mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$LOG_DIR" "$DATABASE_DIR"
    chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR" "$LOG_DIR" "$DATABASE_DIR"
    chmod 755 "$DATABASE_DIR"
    
    echo "Installing server files..."
    cp main.py "$INSTALL_DIR/"
    cp -r src/ "$INSTALL_DIR/"
    cp README.md "$INSTALL_DIR/"
    cp requirements.txt "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/main.py"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    
    echo "Creating configuration file..."
    cat > "$CONFIG_DIR/config.env" << EOF
# SQLite MCP Server Configuration - System Mode
MCP_HOST=$SERVER_HOST
MCP_PORT=$SERVER_PORT
MCP_LOG_LEVEL=INFO
MCP_LOG_DIR=$LOG_DIR
MCP_MAX_CONNECTIONS=20
MCP_MAX_QUERY_TIME=60
MCP_MAX_RESULT_ROWS=10000
EOF

    echo "Creating systemd service..."
    cat > "$SYSTEMD_SERVICE" << EOF
[Unit]
Description=SQLite MCP Server (System Mode)
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

# Enhanced security settings for system mode
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$LOG_DIR $DATABASE_DIR

[Install]
WantedBy=multi-user.target
EOF

    echo "Setting up database directory permissions..."
    echo "To use databases, copy them to: $DATABASE_DIR"
    echo "Or use: sudo cp your_database.db $DATABASE_DIR/ && sudo chown $SERVICE_USER:$SERVICE_USER $DATABASE_DIR/your_database.db"
    
    echo "✅ System mode deployment complete!"
    echo "Configuration: $CONFIG_DIR/config.env"
    echo "Installation: $INSTALL_DIR" 
    echo "Database directory: $DATABASE_DIR"
    echo "Logs: $LOG_DIR"
}

# Execute deployment based on mode
if [[ "$DEPLOY_MODE" == "user" ]]; then
    deploy_user_mode
elif [[ "$DEPLOY_MODE" == "system" ]]; then
    deploy_system_mode
fi

# Final service management
echo ""
echo "🔧 Configuring systemd service..."
systemctl daemon-reload

echo "🚀 Starting and enabling service..."
systemctl enable sqlite-mcp-server
systemctl start sqlite-mcp-server

# Wait a moment for service to start
sleep 2

# Check service status
echo ""
echo "📊 Service Status:"
echo "=================="
systemctl status sqlite-mcp-server --no-pager -l

# Display connection information
echo ""
echo "🎉 Deployment Complete!"
echo "======================="
echo ""
echo "Service: sqlite-mcp-server"
echo "Mode: $DEPLOY_MODE"
echo "Status: $(systemctl is-active sqlite-mcp-server)"
echo "Host: $SERVER_HOST"
echo "Port: $SERVER_PORT"
echo ""
echo "📋 Useful Commands:"
echo "  sudo systemctl status sqlite-mcp-server    # Check status"
echo "  sudo systemctl restart sqlite-mcp-server   # Restart service"
echo "  sudo systemctl stop sqlite-mcp-server      # Stop service"
echo "  sudo journalctl -u sqlite-mcp-server -f    # View logs"
echo ""

if [[ "$DEPLOY_MODE" == "user" ]]; then
    echo "🏠 User Mode Features:"
    echo "  - Runs as user: $ACTUAL_USER"
    echo "  - Can access home directory databases"
    echo "  - Configuration: $USER_HOME/.config/sqlite-mcp-server/"
    echo "  - Logs: $USER_HOME/.local/share/sqlite-mcp-server/logs/"
    echo ""
    echo "💡 To connect to a database in your home directory:"
    echo "   Use full path: /home/$ACTUAL_USER/path/to/your/database.db"
elif [[ "$DEPLOY_MODE" == "system" ]]; then
    echo "🔒 System Mode Features:"
    echo "  - Runs as dedicated user: mcp"
    echo "  - Enhanced security isolation"
    echo "  - Database directory: /var/lib/sqlite-mcp-server/databases/"
    echo "  - Configuration: /etc/sqlite-mcp-server/"
    echo ""
    echo "💡 To use your databases:"
    echo "   sudo cp your_database.db /var/lib/sqlite-mcp-server/databases/"
    echo "   sudo chown mcp:mcp /var/lib/sqlite-mcp-server/databases/your_database.db"
    echo "   Then use path: /var/lib/sqlite-mcp-server/databases/your_database.db"
fi

echo ""
echo "🌐 Test the server:"
echo "   curl http://$SERVER_HOST:$SERVER_PORT/health"
echo ""
