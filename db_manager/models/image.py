# database/models/image.py
import app_logger as logger
from exceptions import InvalidDataError, EntityNotFoundError

class ImageModel:
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
    
    def add(self, image_data):
        """Add an image with specified details"""
        if not image_data:
            raise InvalidDataError("Image data cannot be None or empty")
        
        query = """
        INSERT INTO images (
            bookId, imageUrl, width, height, 
            sizeKb, local_file_path, createdAt, updatedAt
        )
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
        
        params = (
            image_data.get('bookId'),
            image_data.get('imageUrl'),
            image_data.get('width', 0),
            image_data.get('height', 0),
            image_data.get('sizeKb', 0),
            image_data.get('local_file_path')
        )
        
        return self.connection_manager.execute(query, params)
    
    def get_by_book(self, book_id):
        """Get all images for a specific book"""
        results = self.connection_manager.execute(
            "SELECT * FROM images WHERE bookId = ?", 
            (book_id,)
        )
        return results
    
    def update(self, image_id, image_data):
        """Update an image record"""
        query_parts = []
        params = []
        
        updatable_fields = [
            'imageUrl', 'width', 'height', 'sizeKb', 'local_file_path'
        ]
        
        for field in updatable_fields:
            if field in image_data:
                query_parts.append(f"{field} = ?")
                params.append(image_data.get(field))
        
        if not query_parts:
            logger.log_warning(f"No valid fields to update for image {image_id}")
            return False
        
        # Always update the updatedAt timestamp
        query_parts.append("updatedAt = CURRENT_TIMESTAMP")
        
        query = f"UPDATE images SET {', '.join(query_parts)} WHERE id = ?"
        params.append(image_id)
        
        try:
            self.connection_manager.execute(query, params)
            return True
        except Exception as e:
            logger.log_error(f"Error updating image {image_id}: {str(e)}")
            return False
    
    def delete(self, image_id):
        """Delete an image by its ID"""
        try:
            self.connection_manager.execute(
                "DELETE FROM images WHERE id = ?", 
                (image_id,)
            )
            return True
        except Exception as e:
            logger.log_error(f"Error deleting image {image_id}: {str(e)}")
            return False
