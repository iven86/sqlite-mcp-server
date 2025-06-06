"""
Main SQLite MCP Server implementation
"""
import logging
from typing import Any, Dict
from datetime import datetime

from .models import MCPError, ServerStats, ServerCapabilities
from .database import DatabaseManager
from .tools import MCPTools
from .utils import setup_logging, create_json_rpc_response, create_json_rpc_error


class SQLiteMCPServer:
    """MCP-compliant SQLite server for database operations"""
    
    def __init__(self, log_level: str = "INFO"):
        setup_logging(log_level)
        self.logger = logging.getLogger(__name__)
        self.initialized = False
        
        # Initialize components
        self.capabilities = ServerCapabilities()
        self.stats = ServerStats()
        self.db_manager = DatabaseManager()
        self.tools = MCPTools(self.db_manager)
        
        # Production settings (will be updated by config)
        self.max_db_connections = 10
        self.max_query_time = 60.0
        self.max_result_rows = 10000
    
    def update_config(self, config):
        """Update server configuration"""
        self.max_db_connections = config.max_connections
        self.max_query_time = config.max_query_time
        self.max_result_rows = config.max_result_rows
        
        # Update tools configuration
        self.tools.max_query_time = config.max_query_time
        self.tools.max_result_rows = config.max_result_rows
    
    async def handle_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP JSON-RPC request"""
        self.stats.total_requests += 1
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})
        
        self.logger.info(f"MCP Request: {method} (ID: {request_id})")
        
        try:
            if method == "initialize":
                result = await self.initialize(params)
            elif method == "tools/list":
                if not self.initialized:
                    raise MCPError(-32002, "Server not initialized")
                result = await self.list_tools(params)
            elif method == "tools/call":
                if not self.initialized:
                    raise MCPError(-32002, "Server not initialized")
                result = await self.call_tool(params)
            else:
                raise MCPError(-32601, f"Method not found: {method}")
            
            self.stats.successful_requests += 1
            return create_json_rpc_response(request_id, result)
            
        except MCPError as e:
            self.stats.failed_requests += 1
            self.logger.error(f"MCP Error: {e.message}")
            return create_json_rpc_response(
                request_id, 
                error=create_json_rpc_error(e.code, e.message, e.data)
            )
        except Exception as e:
            self.stats.failed_requests += 1
            self.logger.error(f"Unexpected error: {str(e)}")
            return create_json_rpc_response(
                request_id,
                error=create_json_rpc_error(-32603, "Internal error", str(e))
            )
    
    async def initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request"""
        protocol_version = params.get("protocolVersion", "2025-03-26")
        client_info = params.get("clientInfo", {})
        
        self.logger.info(f"Initializing MCP server for client: {client_info.get('name', 'unknown')}")
        
        self.initialized = True
        
        return {
            "protocolVersion": "2025-03-26",
            "capabilities": self.capabilities.to_dict(),
            "serverInfo": {
                "name": "sqlite-mcp-server",
                "version": "1.0.0"
            }
        }
    
    async def list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List available tools"""
        return {"tools": self.tools.get_tool_definitions()}
    
    async def call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            raise MCPError(-32602, "Tool name is required")
        
        self.logger.info(f"Calling tool: {tool_name}")
        
        return await self.tools.execute_tool(tool_name, arguments)
    
    async def health_check(self, params: Dict[str, Any] = {}) -> Dict[str, Any]:
        """Health check endpoint"""
        return {
            "success": True,
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "current_database": str(self.db_manager.current_db_path) if self.db_manager.current_db_path else None,
            "initialized": self.initialized,
            "stats": self.stats.to_dict()
        }
