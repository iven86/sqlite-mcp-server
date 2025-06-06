#!/bin/bash
# SQLite MCP Server - Production Startup Script

# Set script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Configuration
HOST="${MCP_HOST:-localhost}"
PORT="${MCP_PORT:-9999}"
LOG_LEVEL="${MCP_LOG_LEVEL:-INFO}"
MAX_CONNECTIONS="${MCP_MAX_CONNECTIONS:-10}"
MAX_QUERY_TIME="${MCP_MAX_QUERY_TIME:-60}"
MAX_RESULT_ROWS="${MCP_MAX_RESULT_ROWS:-10000}"

# Create logs directory
mkdir -p logs

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed"
    exit 1
fi

# Check if server is already running
if pgrep -f "main.py" > /dev/null; then
    echo "Warning: SQLite MCP Server may already be running"
    echo "Use 'pkill -f main.py' to stop existing processes"
fi

# Function to handle cleanup on exit
cleanup() {
    echo "Stopping SQLite MCP Server..."
    pkill -f "main.py"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo "Starting SQLite MCP Server..."
echo "Host: $HOST"
echo "Port: $PORT"
echo "Log Level: $LOG_LEVEL"
echo "Max Connections: $MAX_CONNECTIONS"
echo "Max Query Time: ${MAX_QUERY_TIME}s"
echo "Max Result Rows: $MAX_RESULT_ROWS"
echo ""

# Start the server with configuration
python3 main.py \
    --host "$HOST" \
    --port "$PORT" \
    --log-level "$LOG_LEVEL" \
    --max-connections "$MAX_CONNECTIONS" \
    --max-query-time "$MAX_QUERY_TIME" \
    --max-result-rows "$MAX_RESULT_ROWS"
