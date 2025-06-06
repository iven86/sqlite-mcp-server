"""
HTTP handler for SQLite MCP Server
"""
import json
import time
import asyncio
from http.server import BaseHTTPRequestHandler


class MCPHTTPHandler(BaseHTTPRequestHandler):
    """Production HTTP handler for MCP server requests"""
    
    mcp_server = None  # Will be set by the main function
    
    def do_POST(self):
        """Handle POST requests with enhanced error handling"""
        start_time = time.time()
        client_ip = self.client_address[0]
        
        try:
            # Check content length
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 10 * 1024 * 1024:  # 10MB limit
                self.send_error(413, "Request too large")
                return
                
            if content_length == 0:
                self.send_error(400, "Empty request body")
                return
            
            # Read and parse request
            post_data = self.rfile.read(content_length)
            try:
                request_data = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError as e:
                self.send_error(400, f"Invalid JSON: {str(e)}")
                return
            
            # Validate JSON-RPC structure
            if not isinstance(request_data, dict) or 'method' not in request_data:
                self.send_error(400, "Invalid JSON-RPC request")
                return
            
            # Log request (without sensitive data)
            method = request_data.get('method', 'unknown')
            request_id = request_data.get('id', 'no-id')
            self.mcp_server.logger.info(f"Request from {client_ip}: {method} (ID: {request_id})")
            
            # Handle async request
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(self.mcp_server.handle_mcp_request(request_data))
            loop.close()
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            
            response_json = json.dumps(response)
            self.wfile.write(response_json.encode('utf-8'))
            
            # Log timing
            elapsed = time.time() - start_time
            if elapsed > 1.0:  # Log slow requests
                self.mcp_server.logger.warning(f"Slow request {method}: {elapsed:.3f}s")
            
        except Exception as e:
            self.mcp_server.logger.error(f"Request handling error from {client_ip}: {str(e)}")
            self.send_error(500, f"Server error: {str(e)}")
    
    def do_GET(self):
        """Handle GET requests for health and status"""
        client_ip = self.client_address[0]
        
        if self.path == '/health':
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = loop.run_until_complete(self.mcp_server.health_check())
                loop.close()
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except Exception as e:
                self.mcp_server.logger.error(f"Health check error: {str(e)}")
                self.send_error(500, f"Health check failed: {str(e)}")
        
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Cache-Control', 'public, max-age=3600')
            self.end_headers()
            
            html = f"""
            <!DOCTYPE html>
            <html><head><title>SQLite MCP Server</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .status {{ background: #e8f5e8; padding: 10px; border-radius: 5px; }}
                .endpoints {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
                ul {{ margin: 10px 0; }}
            </style></head>
            <body>
                <h1>SQLite MCP Server v1.0.0</h1>
                <div class="status">
                    <p><strong>Status:</strong> Running</p>
                    <p><strong>Initialized:</strong> {self.mcp_server.initialized}</p>
                    <p><strong>Current Database:</strong> {self.mcp_server.db_manager.current_db_path or 'None'}</p>
                    <p><strong>Requests Processed:</strong> {self.mcp_server.stats.total_requests}</p>
                </div>
                
                <h3>API Endpoints</h3>
                <div class="endpoints">
                    <ul>
                        <li><strong>POST /</strong> - Main MCP JSON-RPC endpoint</li>
                        <li><strong>GET /health</strong> - Health check and statistics</li>
                        <li><strong>GET /</strong> - This status page</li>
                    </ul>
                </div>
                
                <h3>MCP Methods</h3>
                <div class="endpoints">
                    <ul>
                        <li><strong>initialize</strong> - Initialize MCP connection</li>  
                        <li><strong>tools/list</strong> - List available tools</li>
                        <li><strong>tools/call</strong> - Execute a tool</li>
                    </ul>
                </div>
                
                <h3>Available Tools</h3>
                <div class="endpoints">
                    <ul>
                        <li><strong>connect_database</strong> - Connect to SQLite database</li>
                        <li><strong>query</strong> - Execute SQL queries</li>
                        <li><strong>get_tables</strong> - List database tables</li>
                        <li><strong>get_schema</strong> - Get table schema</li>
                        <li><strong>create, read, update, delete</strong> - CRUD operations</li>
                        <li><strong>analyze_table</strong> - Table analytics</li>
                        <li><strong>search_data</strong> - Search across tables</li>
                    </ul>
                </div>
                
                <hr>
                <p><small>SQLite MCP Server - Production Ready</small></p>
            </body></html>
            """
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_error(404, "Not Found")
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '86400')  # 24 hours
        self.end_headers()
    
    def log_message(self, format, *args):
        """Override default logging to use our logger"""
        if self.mcp_server and hasattr(self.mcp_server, 'logger'):
            self.mcp_server.logger.debug(f"{self.client_address[0]} - {format % args}")
        else:
            # Fallback to default logging
            pass
