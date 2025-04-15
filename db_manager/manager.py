# database/manager.py
import os
import json
import sqlite3
from config import DATABASE_PATH
import app_logger as logger

from .connection import DatabaseConnectionManager
from .schema import initialize_tables
from .models.author import AuthorModel
from .models.book import BookModel
from .models.genre import GenreModel
from .models.publisher import PublisherModel
from .models.image import ImageModel
from .models.settings import SettingsModel

from exceptions import (
    ConnectionError, 
    QueryError, 
    DataIntegrityError, 
    EntityNotFoundError, 
    DuplicateEntityError,
    InvalidDataError, 
    SchemaError
)

class DatabaseManager:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.connection_manager = DatabaseConnectionManager(self.db_path)
        
        # Initialize all models with the connection manager
        self.authors = AuthorModel(self.connection_manager)
        self.books = BookModel(self.connection_manager)
        self.genres = GenreModel(self.connection_manager)
        self.images = ImageModel(self.connection_manager)
        self.publishers = PublisherModel(self.connection_manager)
        self.settings = SettingsModel(self.connection_manager)
    
        self.initialize_db()
    
    def initialize_db(self):
        """Create database tables if they don't exist"""
        # Ensure the database directory exists
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        
        try:
            # Use the connection manager for initialization
            with self.connection_manager.connection() as conn:
                cursor = conn.cursor()
                initialize_tables(cursor)
                conn.commit()
        except Exception as e:
            logger.log_error(f"Database initialization error: {e}")
            raise
            
    def execute_query(self, query, params=None):
        """Legacy method to maintain compatibility with existing code"""
        return self.connection_manager.execute(query, params)
    
    # Process publisher data method (kept at manager level since it involves multiple models)
    def process_publisher_data(self, publisher_json):
        """Process the complete publisher JSON data including catalogue"""
        # Initialize results to track what was imported
        results = {
            'publishers': [],
            'users': [],
            'authors': [], 
            'books': [],
            'images': []
        }
        
        # Process each publisher entry in the JSON array
        for entry in publisher_json:
            # Add the publisher
            publisher = entry.get('publisher')
            if publisher:
                publisher_id = self.publishers.add(publisher)
                results['publishers'].append(publisher.get('id'))
            
            # Process the catalogue
            catalogue = entry.get('catalogue', [])
            for author_entry in catalogue:
                # Add the author
                author = author_entry.get('author')
                if author:
                    # Add the user first if it exists
                    user = author.get('user')
                    if user:
                        # Note: User operations would be handled by a user model in a full implementation
                        # This is simplified for the example
                        user_id = self.execute_query(
                            "INSERT INTO users (id, username, email, displayName) VALUES (?, ?, ?, ?)",
                            (user.get('id'), user.get('username'), user.get('email'), user.get('displayName'))
                        )
                        results['users'].append(user.get('id'))
                    
                    # Then add the author
                    author_id = self.authors.add(author)
                    results['authors'].append(author.get('id'))
                
                # Process all books for this author
                books = author_entry.get('books', [])
                for book in books:
                    # Add the book
                    book_id = self.books.add(book)
                    results['books'].append(book.get('id'))
                    
                    # Add all images for the book
                    images = book.get('images', [])
                    for image in images:
                        image_id = self.images.add(image)
                        results['images'].append(image.get('id'))
        
        return results

