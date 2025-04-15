# database/connection.py
import sqlite3
import contextlib
import app_logger as logger

class DatabaseConnectionManager:
    def __init__(self, db_path):
        self.db_path = db_path

    @contextlib.contextmanager
    def connection(self):
        """
        Context manager for database connections
        Ensures connections are always closed, even if exceptions occur
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            yield conn
        except sqlite3.Error as e:
            logger.log_error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def execute(self, query, params=None, commit=True):
        """
        Execute a query with enhanced error handling and connection management
        
        :param query: SQL query to execute
        :param params: Optional query parameters
        :param commit: Whether to commit the transaction (default True)
        :return: Query results or last row ID
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Determine query type and handle accordingly
                query_type = query.strip().upper().split()[0]
                
                if query_type == "SELECT":
                    return cursor.fetchall()
                else:
                    if commit:
                        conn.commit()
                    return cursor.lastrowid
            
            except sqlite3.Error as e:
                conn.rollback()
                logger.log_error(f"Query execution error: {e}")
                raise
