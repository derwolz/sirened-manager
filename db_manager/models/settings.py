# database/models/settings.py
import app_logger as logger
from exceptions import InvalidDataError

class SettingsModel:
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
    
    def get(self, key, default=None):
        """Get a user setting value"""
        results = self.connection_manager.execute(
            "SELECT value FROM user_settings WHERE key = ?", 
            (key,)
        )
        
        return results[0][0] if results else default
    
    def set(self, key, value, setting_id=None):
        """Set a user setting value"""
        if not key:
            raise InvalidDataError("Setting key cannot be empty")
        
        if setting_id:
            query = """
            INSERT OR REPLACE INTO user_settings (id, key, value, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """
            return self.connection_manager.execute(query, (setting_id, key, value))
        else:
            query = """
            INSERT OR REPLACE INTO user_settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            """
            return self.connection_manager.execute(query, (key, value))
    
    def get_all(self):
        """Get all user settings"""
        return self.connection_manager.execute("SELECT * FROM user_settings")
