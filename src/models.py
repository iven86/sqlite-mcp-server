"""
Data models and error classes for SQLite MCP Server
"""
from typing import Any, Dict


class MCPError(Exception):
    """MCP protocol error"""
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


class ServerConfig:
    """Server configuration class"""
    def __init__(self):
        self.host = 'localhost'
        self.port = 9999
        self.log_level = 'INFO'
        self.max_connections = 10
        self.max_query_time = 60
        self.max_result_rows = 10000
        self.daemon = False
        
        # Production settings
        self.connection_timeout = 30.0
        self.max_db_connections = 10
        
    def update_from_args(self, args):
        """Update configuration from command line arguments"""
        self.host = args.host
        self.port = args.port
        self.log_level = args.log_level
        self.max_connections = args.max_connections
        self.max_query_time = args.max_query_time
        self.max_result_rows = args.max_result_rows
        self.daemon = args.daemon


class ServerStats:
    """Server statistics tracking"""
    def __init__(self):
        from datetime import datetime
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.start_time = datetime.now()
    
    def to_dict(self):
        """Convert stats to dictionary"""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests
        }


class ServerCapabilities:
    """MCP server capabilities"""
    def __init__(self):
        self.capabilities = {
            "tools": {
                "listChanged": False
            }
        }
    
    def to_dict(self):
        """Convert capabilities to dictionary"""
        return self.capabilities
