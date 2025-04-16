# database/models/genre.py
import json
import app_logger as logger
from exceptions import InvalidDataError, EntityNotFoundError

class GenreModel:
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
    
    # Here's a fix for the GenreModel.add() method:
    def add(self, genre_data):
        """Add a genre"""
        if not genre_data:
            raise InvalidDataError("Genre data cannot be None or empty")
        
        query = """
        INSERT OR REPLACE INTO genres (
            id, name, description, type, parentId, 
            createdAt, updatedAt, deletedAt
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            genre_data.get('id'),
            genre_data.get('name'),  # Map 'name' from input to 'genre' in DB
            genre_data.get('description'),
            genre_data.get('type'),
            genre_data.get('parentId'),
            genre_data.get('createdAt'),
            genre_data.get('updatedAt'),
            genre_data.get('deletedAt')
        )
        
        return self.connection_manager.execute(query, params)
    
    def add_book_genre(self, book_id, genre_id, relation_id=None):
        """Associate a genre with a book"""
        if relation_id:
            query = "INSERT OR IGNORE INTO book_genres (id, book_id, genre_id) VALUES (?, ?, ?)"
            return self.connection_manager.execute(query, (relation_id, book_id, genre_id))
        else:
            query = "INSERT OR IGNORE INTO book_genres (book_id, genre_id) VALUES (?, ?)"
            return self.connection_manager.execute(query, (book_id, genre_id))
    
    def get_all(self):
        """Get all genres from the database"""
        return self.connection_manager.execute("SELECT * FROM genres ORDER BY id")
    
    def get(self, genre_id):
        """Get a genre by ID"""
        results = self.connection_manager.execute(
            "SELECT * FROM genres WHERE id = ?", 
            (genre_id,)
        )
        if not results:
            raise EntityNotFoundError(f"Genre with ID {genre_id} not found")
        return results[0]
    
    def get_by_book(self, book_id):
        """Get all genres for a book"""
        query = """
        SELECT g.* 
        FROM genres g
        JOIN book_genres bg ON g.id = bg.genre_id
        WHERE bg.book_id = ?
        """
        return self.connection_manager.execute(query, (book_id,))
    
    def get_subgenres(self, parent_id):
        """Get all subgenres for a parent genre"""
        return self.connection_manager.execute(
            "SELECT * FROM genres WHERE parentId = ?", 
            (parent_id,)
        )
