"""
MCP tool implementations for SQLite operations
"""
import json
import sqlite3
import time
import threading
from typing import Dict, Any
from .models import MCPError


class MCPTools:
    """MCP tool implementations"""
    
    def __init__(self, db_manager, max_query_time=60, max_result_rows=10000):
        self.db_manager = db_manager
        self.max_query_time = max_query_time
        self.max_result_rows = max_result_rows
        
    def get_tool_definitions(self):
        """Get all tool definitions"""
        return [
            {
                "name": "connect_database",
                "description": "Connect to a SQLite database file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "db_path": {
                            "type": "string",
                            "description": "Path to the SQLite database file"
                        }
                    },
                    "required": ["db_path"]
                }
            },
            {
                "name": "query",
                "description": "Execute a SQL query on the connected database",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "SQL query to execute"
                        },
                        "params": {
                            "type": "array",
                            "description": "Parameters for the SQL query",
                            "items": {"type": "string"}
                        },
                        "db_path": {
                            "type": "string",
                            "description": "Optional: database path (uses connected DB if not specified)"
                        }
                    },
                    "required": ["sql"]
                }
            },
            {
                "name": "get_tables",
                "description": "Get list of all tables in the database",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "db_path": {
                            "type": "string",
                            "description": "Optional: database path (uses connected DB if not specified)"
                        }
                    }
                }
            },
            {
                "name": "get_schema",
                "description": "Get schema information for a specific table",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "table": {
                            "type": "string",
                            "description": "Name of the table"
                        },
                        "db_path": {
                            "type": "string",
                            "description": "Optional: database path (uses connected DB if not specified)"
                        }
                    },
                    "required": ["table"]
                }
            },
            {
                "name": "create",
                "description": "Insert a new record into a table",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "table": {
                            "type": "string",
                            "description": "Name of the table"
                        },
                        "data": {
                            "type": "object",
                            "description": "Data to insert (column: value pairs)"
                        },
                        "db_path": {
                            "type": "string",
                            "description": "Optional: database path (uses connected DB if not specified)"
                        }
                    },
                    "required": ["table", "data"]
                }
            },
            {
                "name": "read",
                "description": "Read records from a table with optional filtering",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "table": {
                            "type": "string",
                            "description": "Name of the table"
                        },
                        "where": {
                            "type": "object",
                            "description": "WHERE conditions (column: value pairs)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of records to return"
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Number of records to skip"
                        },
                        "order_by": {
                            "type": "string",
                            "description": "ORDER BY clause"
                        },
                        "db_path": {
                            "type": "string",
                            "description": "Optional: database path (uses connected DB if not specified)"
                        }
                    },
                    "required": ["table"]
                }
            },
            {
                "name": "update",
                "description": "Update records in a table",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "table": {
                            "type": "string",
                            "description": "Name of the table"
                        },
                        "data": {
                            "type": "object",
                            "description": "Data to update (column: value pairs)"
                        },
                        "where": {
                            "type": "object",
                            "description": "WHERE conditions (column: value pairs)"
                        },
                        "db_path": {
                            "type": "string",
                            "description": "Optional: database path (uses connected DB if not specified)"
                        }
                    },
                    "required": ["table", "data", "where"]
                }
            },
            {
                "name": "delete",
                "description": "Delete records from a table",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "table": {
                            "type": "string",
                            "description": "Name of the table"
                        },
                        "where": {
                            "type": "object",
                            "description": "WHERE conditions (column: value pairs)"
                        },
                        "db_path": {
                            "type": "string",
                            "description": "Optional: database path (uses connected DB if not specified)"
                        }
                    },
                    "required": ["table", "where"]
                }
            },
            {
                "name": "analyze_table",
                "description": "Analyze table statistics and sample data",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "table": {
                            "type": "string",
                            "description": "Name of the table"
                        },
                        "db_path": {
                            "type": "string",
                            "description": "Optional: database path (uses connected DB if not specified)"
                        }
                    },
                    "required": ["table"]
                }
            },
            {
                "name": "search_data",
                "description": "Search for data across multiple tables",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "search_term": {
                            "type": "string",
                            "description": "Term to search for"
                        },
                        "tables": {
                            "type": "array",
                            "description": "Optional: specific tables to search (searches all if not specified)",
                            "items": {"type": "string"}
                        },
                        "db_path": {
                            "type": "string",
                            "description": "Optional: database path (uses connected DB if not specified)"
                        }
                    },
                    "required": ["search_term"]
                }
            }
        ]
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name"""
        try:
            if tool_name == "connect_database":
                result = await self._tool_connect_database(arguments)
            elif tool_name == "query":
                result = await self._tool_query(arguments)
            elif tool_name == "get_tables":
                result = await self._tool_get_tables(arguments)
            elif tool_name == "get_schema":
                result = await self._tool_get_schema(arguments)
            elif tool_name == "create":
                result = await self._tool_create(arguments)
            elif tool_name == "read":
                result = await self._tool_read(arguments)
            elif tool_name == "update":
                result = await self._tool_update(arguments)
            elif tool_name == "delete":
                result = await self._tool_delete(arguments)
            elif tool_name == "analyze_table":
                result = await self._tool_analyze_table(arguments)
            elif tool_name == "search_data":
                result = await self._tool_search_data(arguments)
            else:
                raise MCPError(-32601, f"Unknown tool: {tool_name}")
                
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ],
                "isError": False
            }
            
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error executing tool {tool_name}: {str(e)}"
                    }
                ],
                "isError": True
            }
    
    async def _tool_connect_database(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Connect to a SQLite database"""
        db_path = arguments.get("db_path")
        if not db_path:
            raise MCPError(-32602, "db_path is required")
        
        try:
            self.db_manager.set_database(db_path)
            # Test connection
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
            
            return {
                "success": True,
                "message": f"Connected to database: {db_path}",
                "database_path": str(self.db_manager.current_db_path),
                "tables_found": len(tables),
                "tables": tables[:10]  # Limit to first 10 tables
            }
        except Exception as e:
            raise MCPError(-32603, f"Failed to connect to database: {str(e)}")
    
    async def _tool_query(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a SQL query with enhanced safety and performance controls"""
        sql = arguments.get("sql")
        params = arguments.get("params", [])
        db_path = arguments.get("db_path")
        
        if not sql:
            raise MCPError(-32602, "sql is required")
        
        # Basic SQL injection protection
        if not self.db_manager.validate_sql_query(sql):
            raise MCPError(-32603, "Potentially dangerous SQL query rejected")
        
        try:
            start_time = time.time()
            
            with self.db_manager.get_connection(db_path) as conn:
                cursor = conn.cursor()
                
                # Set query timeout
                def timeout_handler():
                    try:
                        conn.interrupt()
                    except:
                        pass
                
                timer = threading.Timer(self.max_query_time, timeout_handler)
                timer.start()
                
                try:
                    cursor.execute(sql, params)
                    
                    if sql.strip().upper().startswith('SELECT'):
                        rows = cursor.fetchall()
                        
                        # Limit result set size
                        if len(rows) > self.max_result_rows:
                            rows = rows[:self.max_result_rows]
                        
                        execution_time = time.time() - start_time
                        
                        return {
                            "success": True,
                            "data": [dict(row) for row in rows],
                            "row_count": len(rows),
                            "execution_time_seconds": round(execution_time, 3),
                            "query": sql
                        }
                    else:
                        conn.commit()
                        execution_time = time.time() - start_time
                        
                        return {
                            "success": True,
                            "affected_rows": cursor.rowcount,
                            "last_row_id": cursor.lastrowid,
                            "execution_time_seconds": round(execution_time, 3),
                            "query": sql
                        }
                finally:
                    timer.cancel()
                    
        except sqlite3.OperationalError as e:
            if "interrupted" in str(e).lower():
                raise MCPError(-32603, f"Query timeout after {self.max_query_time} seconds")
            else:
                raise MCPError(-32603, f"SQL execution failed: {str(e)}")
        except Exception as e:
            raise MCPError(-32603, f"Query execution failed: {str(e)}")
    
    async def _tool_get_tables(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get list of all tables"""
        db_path = arguments.get("db_path")
        
        try:
            with self.db_manager.get_connection(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name, type, sql 
                    FROM sqlite_master 
                    WHERE type IN ('table', 'view') 
                    ORDER BY name
                """)
                
                tables = []
                for row in cursor.fetchall():
                    tables.append({
                        "name": row[0],
                        "type": row[1],
                        "sql": row[2]
                    })
                
                return {
                    "success": True,
                    "tables": tables,
                    "count": len(tables)
                }
                
        except Exception as e:
            raise MCPError(-32603, f"Failed to get tables: {str(e)}")
    
    async def _tool_get_schema(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get schema information for a table"""
        table = arguments.get("table")
        db_path = arguments.get("db_path")
        
        if not table:
            raise MCPError(-32602, "table is required")
        
        try:
            with self.db_manager.get_connection(db_path) as conn:
                cursor = conn.cursor()
                
                # Get table info
                cursor.execute(f"PRAGMA table_info({table})")
                columns = []
                for row in cursor.fetchall():
                    columns.append({
                        "cid": row[0],
                        "name": row[1],
                        "type": row[2],
                        "notnull": bool(row[3]),
                        "default_value": row[4],
                        "pk": bool(row[5])
                    })
                
                # Get foreign keys
                cursor.execute(f"PRAGMA foreign_key_list({table})")
                foreign_keys = []
                for row in cursor.fetchall():
                    foreign_keys.append({
                        "id": row[0],
                        "seq": row[1],
                        "table": row[2],
                        "from": row[3],
                        "to": row[4],
                        "on_update": row[5],
                        "on_delete": row[6],
                        "match": row[7]
                    })
                
                # Get indexes
                cursor.execute(f"PRAGMA index_list({table})")
                indexes = []
                for row in cursor.fetchall():
                    indexes.append({
                        "seq": row[0],
                        "name": row[1],
                        "unique": bool(row[2]),
                        "origin": row[3],
                        "partial": bool(row[4])
                    })
                
                return {
                    "success": True,
                    "table": table,
                    "columns": columns,
                    "foreign_keys": foreign_keys,
                    "indexes": indexes
                }
                
        except Exception as e:
            raise MCPError(-32603, f"Failed to get schema for table {table}: {str(e)}")
    
    async def _tool_create(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new record"""
        table = arguments.get("table")
        data = arguments.get("data", {})
        db_path = arguments.get("db_path")
        
        if not table or not data:
            raise MCPError(-32602, "table and data are required")
        
        try:
            columns = list(data.keys())
            placeholders = ["?" for _ in columns]
            values = list(data.values())
            
            sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            
            with self.db_manager.get_connection(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(sql, values)
                conn.commit()
                
                return {
                    "success": True,
                    "inserted_id": cursor.lastrowid,
                    "affected_rows": cursor.rowcount,
                    "table": table,
                    "data": data
                }
        except Exception as e:
            raise MCPError(-32603, f"Failed to create record in {table}: {str(e)}")
    
    async def _tool_read(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Read records from a table"""
        table = arguments.get("table")
        where = arguments.get("where", {})
        limit = arguments.get("limit")
        offset = arguments.get("offset", 0)
        order_by = arguments.get("order_by")
        db_path = arguments.get("db_path")
        
        if not table:
            raise MCPError(-32602, "table is required")
        
        try:
            sql = f"SELECT * FROM {table}"
            bind_params = []
            
            if where:
                conditions = []
                for key, value in where.items():
                    conditions.append(f"{key} = ?")
                    bind_params.append(value)
                sql += f" WHERE {' AND '.join(conditions)}"
            
            if order_by:
                sql += f" ORDER BY {order_by}"
            
            if limit:
                sql += f" LIMIT {limit}"
                if offset:
                    sql += f" OFFSET {offset}"
            
            with self.db_manager.get_connection(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(sql, bind_params)
                rows = cursor.fetchall()
                
                return {
                    "success": True,
                    "data": [dict(row) for row in rows],
                    "row_count": len(rows),
                    "table": table,
                    "query": sql
                }
        except Exception as e:
            raise MCPError(-32603, f"Failed to read from {table}: {str(e)}")
    
    async def _tool_update(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Update records in a table"""
        table = arguments.get("table")
        data = arguments.get("data", {})
        where = arguments.get("where", {})
        db_path = arguments.get("db_path")
        
        if not table or not data or not where:
            raise MCPError(-32602, "table, data, and where are required")
        
        try:
            set_clauses = []
            set_params = []
            for key, value in data.items():
                set_clauses.append(f"{key} = ?")
                set_params.append(value)
            
            where_clauses = []
            where_params = []
            for key, value in where.items():
                where_clauses.append(f"{key} = ?")
                where_params.append(value)
            
            sql = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE {' AND '.join(where_clauses)}"
            bind_params = set_params + where_params
            
            with self.db_manager.get_connection(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(sql, bind_params)
                conn.commit()
                
                return {
                    "success": True,
                    "affected_rows": cursor.rowcount,
                    "table": table,
                    "data": data,
                    "where": where
                }
        except Exception as e:
            raise MCPError(-32603, f"Failed to update {table}: {str(e)}")
    
    async def _tool_delete(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Delete records from a table"""
        table = arguments.get("table")
        where = arguments.get("where", {})
        db_path = arguments.get("db_path")
        
        if not table or not where:
            raise MCPError(-32602, "table and where are required")
        
        try:
            where_clauses = []
            where_params = []
            for key, value in where.items():
                where_clauses.append(f"{key} = ?")
                where_params.append(value)
            
            sql = f"DELETE FROM {table} WHERE {' AND '.join(where_clauses)}"
            
            with self.db_manager.get_connection(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(sql, where_params)
                conn.commit()
                
                return {
                    "success": True,
                    "affected_rows": cursor.rowcount,
                    "table": table,
                    "where": where
                }
        except Exception as e:
            raise MCPError(-32603, f"Failed to delete from {table}: {str(e)}")
    
    async def _tool_analyze_table(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze table statistics and sample data"""
        table = arguments.get("table")
        db_path = arguments.get("db_path")
        
        if not table:
            raise MCPError(-32602, "table is required")
        
        try:
            with self.db_manager.get_connection(db_path) as conn:
                cursor = conn.cursor()
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                
                # Get column info
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [{"name": row[1], "type": row[2]} for row in cursor.fetchall()]
                
                # Get sample data
                cursor.execute(f"SELECT * FROM {table} LIMIT 5")
                sample_data = [dict(row) for row in cursor.fetchall()]
                
                # Get column statistics for numeric columns
                column_stats = {}
                for col in columns:
                    if col["type"].upper() in ["INTEGER", "REAL", "NUMERIC"]:
                        try:
                            cursor.execute(f"SELECT MIN({col['name']}), MAX({col['name']}), AVG({col['name']}) FROM {table}")
                            min_val, max_val, avg_val = cursor.fetchone()
                            column_stats[col["name"]] = {
                                "min": min_val,
                                "max": max_val,
                                "avg": round(avg_val, 2) if avg_val else None
                            }
                        except:
                            pass
                
                return {
                    "success": True,
                    "table": table,
                    "row_count": row_count,
                    "columns": columns,
                    "sample_data": sample_data,
                    "column_statistics": column_stats
                }
        except Exception as e:
            raise MCPError(-32603, f"Failed to analyze table {table}: {str(e)}")
    
    async def _tool_search_data(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Search for data across multiple tables"""
        search_term = arguments.get("search_term")
        tables = arguments.get("tables")
        db_path = arguments.get("db_path")
        
        if not search_term:
            raise MCPError(-32602, "search_term is required")
        
        try:
            with self.db_manager.get_connection(db_path) as conn:
                cursor = conn.cursor()
                
                # Get all tables if not specified
                if not tables:
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                
                results = {}
                for table in tables:
                    try:
                        # Get text columns
                        cursor.execute(f"PRAGMA table_info({table})")
                        text_columns = [row[1] for row in cursor.fetchall() 
                                      if row[2].upper() in ['TEXT', 'VARCHAR', 'CHAR']]
                        
                        if text_columns:
                            # Build search query
                            where_clauses = [f"{col} LIKE ?" for col in text_columns]
                            search_sql = f"SELECT * FROM {table} WHERE {' OR '.join(where_clauses)} LIMIT 10"
                            search_params = [f"%{search_term}%" for _ in text_columns]
                            
                            cursor.execute(search_sql, search_params)
                            matches = [dict(row) for row in cursor.fetchall()]
                            
                            if matches:
                                results[table] = matches
                                
                    except Exception as e:
                        continue
                
                return {
                    "success": True,
                    "search_term": search_term,
                    "results": results,
                    "matches_found": sum(len(matches) for matches in results.values())
                }
        except Exception as e:
            raise MCPError(-32603, f"Failed to search data: {str(e)}")
