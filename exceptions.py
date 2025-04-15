class AuthorProcessingError(Exception):
    """Exception raised when author processing fails"""
    pass

class DatabaseError(Exception):
    """Exception raised when database operations fail"""
    pass

class ImageDownloadError(Exception):
    """Exception raised when image download fails"""
    pass

class ValidationError(Exception):
    """Exception raised when input validation fails"""
    pass

class ConfigurationError(Exception):
    """Exception raised when a required component is missing or misconfigured"""
    pass


class ConnectionError(DatabaseError):
    """Exception raised when database connection fails"""
    pass

class QueryError(DatabaseError):
    """Exception raised when a query fails to execute"""
    pass

class DataIntegrityError(DatabaseError):
    """Exception raised when data doesn't meet integrity constraints"""
    pass

class EntityNotFoundError(DatabaseError):
    """Exception raised when an entity is not found in the database"""
    pass

class DuplicateEntityError(DatabaseError):
    """Exception raised when attempting to create a duplicate entity"""
    pass

class InvalidDataError(DatabaseError):
    """Exception raised when invalid data is provided"""
    pass

class SchemaError(DatabaseError):
    """Exception raised when there's an issue with the database schema"""
    pass
