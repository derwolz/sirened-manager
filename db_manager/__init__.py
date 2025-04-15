# database/__init__.py
"""
Book catalog database module.
"""
from .connection import DatabaseConnectionManager
from .manager import DatabaseManager

# Export the main classes
__all__ = ['DatabaseConnectionManager', 'DatabaseManager']
