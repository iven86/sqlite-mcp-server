"""
SQLite MCP Server Package
A modular, production-ready Model Context Protocol (MCP) server for SQLite database operations
"""

__version__ = "1.0.0"
__author__ = "Assistant"

from .server import SQLiteMCPServer
from .models import MCPError, ServerConfig
from .database import DatabaseManager
from .tools import MCPTools

__all__ = [
    'SQLiteMCPServer',
    'MCPError', 
    'ServerConfig',
    'DatabaseManager',
    'MCPTools'
]
