"""
Utility functions for data synchronization.
"""

import json
import app_logger as logger

def serialize_complex_data(data_dict):
    """
    Convert complex types (lists, dicts) in a dictionary to JSON strings
    
    Args:
        data_dict (dict): Dictionary containing mixed data types
        
    Returns:
        dict: Dictionary with complex types converted to JSON strings
    """
    result = {}
    
    for key, value in data_dict.items():
        if isinstance(value, (list, dict)):
            try:
                result[key] = json.dumps(value)
            except (TypeError, ValueError) as e:
                logger.log_warning(f"Error serializing {key}: {e}")
                result[key] = str(value)
        else:
            result[key] = value
            
    return result

def deserialize_json_field(value, default=None):
    """
    Try to parse a JSON string, return default if fails
    
    Args:
        value (str): JSON string to parse
        default: Default value to return if parsing fails
        
    Returns:
        Parsed value or default value
    """
    if not value or not isinstance(value, str):
        return default
        
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError) as e:
        # If it's a comma-separated list, convert to list
        if isinstance(value, str) and "," in value:
            return value.split(",")
        return default

def map_api_to_db_fields(api_data, field_mapping):
    """
    Map API field names to database field names using a mapping dictionary
    
    Args:
        api_data (dict): Data from the API
        field_mapping (dict): Mapping of API field names to DB field names
        
    Returns:
        dict: Data with field names mapped to database columns
    """
    result = {}
    
    for api_field, db_field in field_mapping.items():
        if api_field in api_data:
            result[db_field] = api_data[api_field]
            
    return result

def get_local_id_for_remote(db_manager, entity_type, remote_id):
    """
    Get the local database ID for a remote entity ID
    
    Args:
        db_manager: Database manager instance
        entity_type (str): Type of entity ('author', 'book', etc.)
        remote_id: The remote ID from the API
        
    Returns:
        int or None: Local ID if found, None otherwise
    """
    if not remote_id:
        return None
        
    setting_key = f"{entity_type}_api_id_{remote_id}"
    local_id = db_manager.get_setting(setting_key)
    
    if local_id:
        try:
            return int(local_id)
        except (ValueError, TypeError):
            logger.log_error(f"Invalid local ID format for {setting_key}: {local_id}")
            
    return None

def create_timestamp():
    """
    Create a formatted timestamp for logging
    
    Returns:
        str: Formatted timestamp
    """
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def compare_versions(data1, data2, fields_to_check):
    """
    Compare two versions of the same entity to check if update is needed
    
    Args:
        data1 (dict): First data set
        data2 (dict): Second data set
        fields_to_check (list): List of fields to compare
        
    Returns:
        tuple: (bool, dict) - Whether update is needed and changed fields
    """
    changed = False
    changes = {}
    
    for field in fields_to_check:
        if field in data1 and field in data2:
            # Compare values, handling JSON strings
            val1 = data1[field]
            val2 = data2[field]
            
            # Try to parse JSON if needed
            if isinstance(val1, str) and isinstance(val2, (list, dict)):
                try:
                    val1 = json.loads(val1)
                except (json.JSONDecodeError, TypeError):
                    pass
            elif isinstance(val2, str) and isinstance(val1, (list, dict)):
                try:
                    val2 = json.loads(val2)
                except (json.JSONDecodeError, TypeError):
                    pass
                    
            if val1 != val2:
                changed = True
                changes[field] = (val1, val2)
    
    return changed, changes
