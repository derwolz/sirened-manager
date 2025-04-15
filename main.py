import tkinter as tk
import os
from book_catalog_formatter import BookCatalogFormatter
from database_manager import DatabaseManager

def ensure_directory_structure():
    """Ensure all required directories exist"""
    from config import UPLOAD_FOLDER, EXPORT_FOLDER
    
    directories = [UPLOAD_FOLDER, EXPORT_FOLDER]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

if __name__ == "__main__":
    # Initialize directory structure
    ensure_directory_structure()
    
    # Initialize database
    db_manager = DatabaseManager()
    
    # Create main application window
    root = tk.Tk()
    
    # Initialize application with database
    app = BookCatalogFormatter(root, db_manager)
    
    # Start the main event loop
    root.mainloop()
