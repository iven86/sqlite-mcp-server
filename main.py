#!/usr/bin/env python3
"""
SQLite MCP Server - Main Entry Point
A production-ready Model Context Protocol (MCP) server for SQLite database operations
"""
import sys
import signal
import argparse
import threading
import time
from http.server import HTTPServer

from src.models import ServerConfig
from src.server import SQLiteMCPServer
from src.http_handler import MCPHTTPHandler


def main():
    """Main server function with production features"""
    parser = argparse.ArgumentParser(
        description='SQLite MCP HTTP Server - Production Ready',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--host', default='localhost', 
                       help='Server host (use 0.0.0.0 for all interfaces)')
    parser.add_argument('--port', type=int, default=9999, 
                       help='Server port')
    parser.add_argument('--log-level', default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    parser.add_argument('--max-connections', type=int, default=10,
                       help='Maximum database connections')
    parser.add_argument('--max-query-time', type=int, default=60,
                       help='Maximum query execution time in seconds')
    parser.add_argument('--max-result-rows', type=int, default=10000,
                       help='Maximum number of rows to return')
    parser.add_argument('--daemon', action='store_true',
                       help='Run as daemon (background process)')
    
    args = parser.parse_args()
    
    # Create server configuration
    config = ServerConfig()
    config.update_from_args(args)
    
    # Create MCP server with configuration
    mcp_server = SQLiteMCPServer(log_level=config.log_level)
    mcp_server.update_config(config)
    
    # Create HTTP handler class with mcp_server injected
    MCPHTTPHandler.mcp_server = mcp_server
    
    # Create HTTP server
    try:
        http_server = HTTPServer((config.host, config.port), MCPHTTPHandler)
    except OSError as e:
        print(f"Error: Cannot bind to {config.host}:{config.port} - {e}")
        sys.exit(1)
    
    # Flag for graceful shutdown
    shutdown_flag = threading.Event()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        signal_name = "SIGINT" if signum == signal.SIGINT else f"Signal {signum}"
        mcp_server.logger.info(f"Received {signal_name}, shutting down gracefully...")
        print(f"\nReceived {signal_name}, shutting down...")
        shutdown_flag.set()
        http_server.shutdown()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start server
    server_url = f"http://{config.host}:{config.port}"
    print(f"SQLite MCP Server v1.0.0 starting...")
    print(f"Server URL: {server_url}")
    print(f"Health check: {server_url}/health")
    print(f"Status page: {server_url}/")
    print(f"Log level: {config.log_level}")
    print(f"Max connections: {config.max_connections}")
    print(f"Max query time: {config.max_query_time}s")
    print(f"Max result rows: {config.max_result_rows}")
    
    if config.daemon:
        print("Running in daemon mode...")
    else:
        print("Press Ctrl+C to stop")
    
    mcp_server.logger.info(f"Server started on {server_url}")
    
    try:
        # Run server in a separate thread to allow for proper signal handling
        server_thread = threading.Thread(target=http_server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        # Wait for shutdown signal
        while not shutdown_flag.is_set():
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nShutdown requested...")
        shutdown_flag.set()
    except Exception as e:
        mcp_server.logger.error(f"Server error: {e}")
        print(f"Server error: {e}")
        shutdown_flag.set()
    finally:
        mcp_server.logger.info("Server shutdown complete")
        http_server.server_close()
        print("Server stopped.")


if __name__ == "__main__":
    main()
