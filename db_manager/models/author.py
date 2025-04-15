# database/models/author.py
import json
import app_logger as logger
from exceptions import InvalidDataError, DataIntegrityError, EntityNotFoundError

class AuthorModel:
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
    
    def add(self, author_data):
        """Add an author with specified ID"""
        if not author_data:
            raise InvalidDataError("Author data cannot be None or empty")
                
        if not author_data.get('author_name'):
            raise InvalidDataError("Author must have a name")
        
        logger.log_debug(f"adding author {author_data}")
        
        query = """
        INSERT INTO authors (
            id, userId, author_name, author_image_url, 
            birth_date, death_date, website, bio, local_image_path
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            author_data.get('id'),
            author_data.get('userId'),
            author_data.get('author_name'),
            author_data.get('author_image_url'),
            author_data.get('birth_date'),
            author_data.get('death_date'),
            author_data.get('website'),
            author_data.get('bio'),
            author_data.get('local_image_path')
        )
        
        return self.connection_manager.execute(query, params)
    
    def get_all(self):
        """Get all authors from the database"""
        return self.connection_manager.execute("SELECT * FROM authors")
    
    def get(self, author_id):
        """Get a single author by ID"""
        results = self.connection_manager.execute(
            "SELECT * FROM authors WHERE id = ?", 
            (author_id,)
        )
        if not results:
            raise EntityNotFoundError(f"Author with ID {author_id} not found")
        return results[0]
    
    def get_with_user(self, author_id):
        """Get a single author with user information"""
        query = """
        SELECT a.*, u.username, u.email, u.displayName
        FROM authors a
        JOIN users u ON a.userId = u.id
        WHERE a.id = ?
        """
        results = self.connection_manager.execute(query, (author_id,))
        if not results:
            raise EntityNotFoundError(f"Author with ID {author_id} not found")
        return results[0]
    
    def update(self, author_id, author_data):
        """Update an author record"""
        query_parts = []
        params = []
        
        updatable_fields = [
            'author_name', 'author_image_url', 'birth_date', 
            'death_date', 'website', 'bio', 'local_image_path'
        ]
        
        for field in updatable_fields:
            if field in author_data:
                query_parts.append(f"{field} = ?")
                params.append(author_data.get(field))
        
        if not query_parts:
            logger.log_warning(f"No valid fields to update for author {author_id}")
            return False
        
        query = f"UPDATE authors SET {', '.join(query_parts)} WHERE id = ?"
        params.append(author_id)
        
        try:
            self.connection_manager.execute(query, params)
            return True
        except Exception as e:
            logger.log_error(f"Error updating author {author_id}: {str(e)}")
            return False
    
    def get_books(self, author_id):
        """Get all books by an author"""
        query = "SELECT * FROM books WHERE authorId = ?"
        return self.connection_manager.execute(query, (author_id,))
