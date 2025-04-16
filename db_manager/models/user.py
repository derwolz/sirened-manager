import app_logger as logger
from exceptions import InvalidDataError, EntityNotFoundError

class UserModel:
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
    
    def add(self, user_data):
        """Add a user with specified details"""
        if not user_data:
            raise InvalidDataError("User data cannot be None or empty")
        
        if not user_data.get('username') and not user_data.get('email'):
            raise InvalidDataError("User must have either a username or email")
        
        query = """
        INSERT OR REPLACE INTO users (
            id, name, description, email, phone,  
            address, website, logo_url, 
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        
        params = (
            user_data.get('id'),
            user_data.get('name'),
            user_data.get('description'),
            user_data.get('email'),
            user_data.get('phone'),
            user_data.get('address'),
            user_data.get('website'),
            user_data.get('logo_url'),
        )
        
        return self.connection_manager.execute(query, params)
    
    def get_by_id(self, user_id):
        """Get a user by their ID"""
        if not user_id:
            raise InvalidDataError("User ID cannot be None or empty")
        
        query = """
        SELECT id, name, description, email, phone, 
               address, website, logo_url, created_at
        FROM users
        WHERE id = ?
        """
        
        result = self.connection_manager.fetch_one(query, (user_id,))
        if not result:
            raise EntityNotFoundError(f"User with ID {user_id} not found")
        
        return result
    
    def get_by_email(self, email):
        """Get a user by their email address"""
        if not email:
            raise InvalidDataError("Email cannot be None or empty")
        
        query = """
        SELECT id, name, description, email, phone, 
               address, website, logo_url, created_at
        FROM users
        WHERE email = ?
        """
        
        result = self.connection_manager.fetch_one(query, (email,))
        if not result:
            raise EntityNotFoundError(f"User with email {email} not found")
        
        return result
    
    def get_all(self, limit=100, offset=0):
        """Get all users with pagination"""
        query = """
        SELECT id, name, description, email, phone, 
               address, website, logo_url, created_at
        FROM users
        ORDER BY name
        LIMIT ? OFFSET ?
        """
        
        return self.connection_manager.fetch_all(query, (limit, offset))
    
    def update(self, user_id, update_data):
        """Update a user's information"""
        if not user_id:
            raise InvalidDataError("User ID cannot be None or empty")
        
        if not update_data:
            raise InvalidDataError("Update data cannot be None or empty")
        
        # Verify the user exists
        self.get_by_id(user_id)
        
        # Build the query dynamically based on what fields are being updated
        fields = []
        params = []
        
        if 'name' in update_data:
            fields.append("name = ?")
            params.append(update_data['name'])
        
        if 'description' in update_data:
            fields.append("description = ?")
            params.append(update_data['description'])
        
        if 'email' in update_data:
            fields.append("email = ?")
            params.append(update_data['email'])
        
        if 'phone' in update_data:
            fields.append("phone = ?")
            params.append(update_data['phone'])
        
        if 'address' in update_data:
            fields.append("address = ?")
            params.append(update_data['address'])
        
        if 'website' in update_data:
            fields.append("website = ?")
            params.append(update_data['website'])
        
        if 'logo_url' in update_data:
            fields.append("logo_url = ?")
            params.append(update_data['logo_url'])
        
        if not fields:
            logger.warning(f"No fields to update for user {user_id}")
            return False
        
        query = f"""
        UPDATE users
        SET {', '.join(fields)}
        WHERE id = ?
        """
        
        params.append(user_id)
        
        result = self.connection_manager.execute(query, tuple(params))
        return result > 0
    

