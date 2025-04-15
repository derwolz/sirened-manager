# database/models/publisher.py
import app_logger as logger
from exceptions import InvalidDataError, EntityNotFoundError

class PublisherModel:
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
    
    def add(self, publisher_data):
        """Add a publisher"""
        if not publisher_data:
            raise InvalidDataError("Publisher data cannot be None or empty")
        
        logger.log_debug(f"Adding publisher: {publisher_data}")
        
        query = """
        INSERT INTO publishers (
            id, userId, name, publisher_name, publisher_description, 
            business_email, business_phone, business_address, 
            description, website, logoUrl, createdAt
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            publisher_data.get('id'),
            publisher_data.get('userId'),
            publisher_data.get('name'),
            publisher_data.get('publisher_name'),
            publisher_data.get('publisher_description'),
            publisher_data.get('business_email'),
            publisher_data.get('business_phone'),
            publisher_data.get('business_address'),
            publisher_data.get('description'),
            publisher_data.get('website'),
            publisher_data.get('logoUrl'),
            publisher_data.get('createdAt')
        )
        
        return self.connection_manager.execute(query, params)
    
    def get_all(self):
        """Get all publishers"""
        return self.connection_manager.execute("SELECT * FROM publishers")
    
    def get(self, publisher_id):
        """Get a publisher by ID"""
        results = self.connection_manager.execute(
            "SELECT * FROM publishers WHERE id = ?", 
            (publisher_id,)
        )
        if not results:
            raise EntityNotFoundError(f"Publisher with ID {publisher_id} not found")
        return results[0]
    
    def update(self, publisher_id, publisher_data):
        """Update a publisher record"""
        query_parts = []
        params = []
        
        updatable_fields = [
            'name', 'publisher_name', 'publisher_description', 
            'business_email', 'business_phone', 'business_address', 
            'description', 'website', 'logoUrl'
        ]
        
        for field in updatable_fields:
            if field in publisher_data:
                query_parts.append(f"{field} = ?")
                params.append(publisher_data.get(field))
        
        if not query_parts:
            logger.log_warning(f"No valid fields to update for publisher {publisher_id}")
            return False
        
        query = f"UPDATE publishers SET {', '.join(query_parts)} WHERE id = ?"
        params.append(publisher_id)
        
        try:
            self.connection_manager.execute(query, params)
            return True
        except Exception as e:
            logger.log_error(f"Error updating publisher {publisher_id}: {str(e)}")
            return False
