# SQLite MCP Server

A modular Model Context Protocol (MCP) server for SQLite database operations with HTTP API support.

## Project Information

- **Version:** 1.0.0
- **License:** CC BY-NC-SA 4.0 (Non-Commercial)
- **Python:** 3.8+ (Tested on 3.12.3)
- **Dependencies:** Python standard library only

## Overview

SQLite MCP Server implements the Model Context Protocol specification for secure SQLite database operations. It provides a RESTful HTTP API that integrates seamlessly with VS Code and AI agents for database management tasks.

### Key Features

- **Modular Architecture** - Clean separation of concerns with dedicated modules
- **HTTP API** - RESTful endpoints following MCP protocol
- **Security First** - SQL injection protection, query validation, timeout controls
- **System Integration** - Comprehensive logging, graceful shutdown, systemd support
- **Multi-Database** - Support for multiple SQLite database connections
- **AI Integration** - Compatible with VS Code MCP settings for AI agent interactions

## Quick Start

### Prerequisites

- Python 3.8+ (Tested on Python 3.12.3)
- No external dependencies required

### Installation & Basic Usage

```bash
# Start the server
python3 main.py

# Or use the start script (Linux/macOS)
chmod +x scripts/start_server.sh
./scripts/start_server.sh
```

### Quick Test

```bash
# Health check
curl http://localhost:9999/health

# List available tools
curl -X POST http://localhost:9999/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": "1"}'
```

## Available Tools

| Tool | Description | Use Case |
|------|-------------|----------|
| `connect_database` | Connect to a SQLite database file | Database connection |
| `query` | Execute SQL queries with parameters | Data retrieval and operations |
| `get_tables` | List all tables in database | Schema exploration |
| `get_schema` | Get table schema information | Schema inspection |
| `create` | Insert new records into tables | Data creation |
| `read` | Read records with filtering and sorting | Data retrieval |
| `update` | Update existing records | Data modification |
| `delete` | Delete records from tables | Data deletion |
| `analyze_table` | Get table statistics and analysis | Performance analysis |
| `search_data` | Search across multiple tables | Data discovery |

## VS Code Integration

Add to your VS Code `settings.json`:

```json
{
  "mcp": {
    "servers": {
      "sqlite-database": {
        "url": "http://localhost:9999"
      }
    }
  }
}
```

Then ask AI agents:
- "Show me all tables in the database"
- "Execute this SQL query: SELECT * FROM users LIMIT 10"
- "What's the schema of the products table?"

## Architecture

The project follows a modular structure:

```
sqlite_mcp_server/
├── LICENSE              # MIT license file
├── main.py              # Entry point and CLI parsing
├── README.md            # Project documentation
├── requirements.txt     # Python dependencies
├── src/                 # Core MCP modules
│   ├── __init__.py      # Package initialization
│   ├── server.py        # Core MCP server implementation
│   ├── tools.py         # MCP tool definitions and handlers
│   ├── http_handler.py  # HTTP request/response handling
│   ├── database.py      # Database operations and utilities
│   ├── models.py        # Data models and error classes
│   └── utils.py         # Common utility functions
├── scripts/
│   ├── start_server.sh  # Server startup script
│   └── deploy.sh        # System deployment script
├── logs/               # Server logs directory
└── wiki/               # Documentation files
    ├── API-Reference
    ├── Configuration
    ├── Contributing
    ├── Examples
    ├── Getting-Started
    ├── Production-Deployment
    └── Troubleshooting
```

## Documentation

- **[Getting Started](wiki/Getting-Started)** - Installation and setup guide
- **[Configuration](wiki/Configuration)** - Configuration reference
- **[API Reference](wiki/API-Reference)** - API documentation and MCP tools
- **[Examples](wiki/Examples)** - Usage examples and code samples
- **[System Deployment](wiki/Production-Deployment)** - Service setup and management
- **[Troubleshooting](wiki/Troubleshooting)** - Common issues and solutions
- **[Contributing](wiki/Contributing)** - Development guide

## System Deployment

```bash
# Deploy as systemd service
sudo ./scripts/deploy.sh

# Service management
sudo systemctl start sqlite-mcp-server
sudo systemctl enable sqlite-mcp-server
sudo systemctl status sqlite-mcp-server
```

## Security Features

- SQL injection protection with parameterized queries
- Query validation and timeout controls  
- Result size limits to prevent memory exhaustion
- File access control for database security
- Request size limits to prevent DoS attacks

## Contributing

See the [Contributing Guide](wiki/Contributing) for development setup, code standards, testing requirements, and pull request process.

## License

This project is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. Commercial use requires explicit permission from the author. See the [LICENSE](LICENSE) file for details.

## Links

- **[Wiki Documentation](wiki/)** - Complete project documentation
- **[MCP Protocol Specification](https://spec.modelcontextprotocol.io/)** - Model Context Protocol details

---

For help, check the [Troubleshooting Guide](wiki/Troubleshooting).

---

## Support the Project
<a href="https://www.paypal.com/donate?hosted_button_id=QX3V7C8BAJ84S" target="_blank">
  <img src="https://img.shields.io/badge/Donate-PayPal-blue.svg" alt="Donate" width="180">
</a>