"""
Configuration and utility functions for SQLite MCP Server
"""
import logging
import sys
import os
from pathlib import Path
from datetime import datetime


def setup_logging(level: str):
    """Setup production logging"""
    # Use environment variable for log directory, fallback to local logs
    log_dir_path = os.environ.get('MCP_LOG_DIR', 'logs')
    log_dir = Path(log_dir_path)
    
    # Create logs directory if it doesn't exist and we have permission
    try:
        log_dir.mkdir(exist_ok=True)
    except (OSError, PermissionError):
        # If we can't create the directory, fall back to system temp or current dir
        if log_dir_path != 'logs':
            print(f"Warning: Cannot create log directory {log_dir_path}, falling back to local logs")
            log_dir = Path("logs")
            try:
                log_dir.mkdir(exist_ok=True)
            except (OSError, PermissionError):
                # Last resort: use system temp directory
                log_dir = Path("/tmp/sqlite-mcp-server")
                log_dir.mkdir(exist_ok=True)
    
    # Configure logging with both file and console handlers
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / f"mcp_server_{datetime.now().strftime('%Y%m%d')}.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def create_json_rpc_response(request_id, result=None, error=None):
    """Create JSON-RPC 2.0 response"""
    response = {
        "jsonrpc": "2.0",
        "id": request_id
    }
    
    if error:
        response["error"] = error
    else:
        response["result"] = result
        
    return response


def create_json_rpc_error(code: int, message: str, data=None):
    """Create JSON-RPC 2.0 error"""
    error = {
        "code": code,
        "message": message
    }
    if data is not None:
        error["data"] = data
    return error
