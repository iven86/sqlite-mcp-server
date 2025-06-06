"""
Database utilities and connection management for SQLite MCP Server
"""
import sqlite3
import os
import logging
from pathlib import Path
from contextlib import contextmanager
from .models import MCPError


class DatabaseManager:
    """Database connection and operation manager"""
    
    def __init__(self, connection_timeout=30.0):
        self.logger = logging.getLogger(__name__)
        self.current_db_path = None
        self.connection_timeout = connection_timeout
    
    def set_database(self, db_path: str):
        """Set the current database path with validation"""
        db_file = Path(db_path).resolve()
        
        # Security check: ensure the database file is accessible
        if not db_file.exists():
            raise FileNotFoundError(f"Database file not found: {db_path}")
        
        # Check if file is readable
        if not os.access(db_file, os.R_OK):
            raise PermissionError(f"Database file is not readable: {db_path}")
        
        # Check file size (warn if very large)
        file_size = db_file.stat().st_size / (1024 * 1024)  # MB
        if file_size > 1000:  # Warn if larger than 1GB
            self.logger.warning(f"Large database file detected: {file_size:.1f}MB")
        
        self.current_db_path = db_file
        self.logger.info(f"Database set to: {self.current_db_path}")
    
    @contextmanager
    def get_connection(self, db_path: str = None):
        """Get database connection with enhanced error handling"""
        if db_path:
            db_file = Path(db_path).resolve()
        elif self.current_db_path:
            db_file = self.current_db_path
        else:
            raise ValueError("No database path specified")
        
        if not db_file.exists():
            raise FileNotFoundError(f"Database file not found: {db_file}")
        
        conn = None
        try:
            # Enhanced connection settings for production
            conn = sqlite3.connect(
                str(db_file), 
                timeout=self.connection_timeout,
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row
            
            # Set pragmas for better performance and consistency
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")  # Better concurrency
            conn.execute("PRAGMA synchronous = NORMAL")  # Good balance
            conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
            conn.execute("PRAGMA temp_store = memory")
            
            yield conn
        except sqlite3.Error as e:
            self.logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def validate_sql_query(self, sql: str) -> bool:
        """Basic SQL injection protection"""
        sql_upper = sql.strip().upper()
        
        # Block truly dangerous operations
        dangerous_keywords = ['DROP DATABASE', 'DROP SCHEMA', 'TRUNCATE', 'PRAGMA']
        
        # Allow common DML operations (SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, ALTER TABLE)
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return False
        
        # Basic checks for obvious SQL injection patterns
        if any(pattern in sql_upper for pattern in [';--', '/*', '*/', 'UNION SELECT', 'EXEC(', 'EXECUTE(']):
            return False
            
        return True
