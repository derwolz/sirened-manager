"""
Author data processing functionality.
"""

import requests
import sqlite3
import app_logger as logger
from exceptions import AuthorProcessingError, DatabaseError

class AuthorProcessor:
    """
    Handles processing and storing author data
    """
    def __init__(self, db_manager, synchronizer):
        self.db_manager = db_manager
        self.synchronizer = synchronizer
        
    def process_author(self, author_info):
        """Process and store author data in the database"""
        try:
            if not author_info:
                raise ValueError("Author information cannot be None or empty")
            
            # Extract author data
            api_author_id = author_info.get("id")
            if not api_author_id:
                raise ValueError("Author must have an ID")
                
            author_name = author_info.get("author_name", "")
            if not author_name:
                raise ValueError("Author must have a name")
                
            author_image_url = author_info.get("author_image_url")
            birth_date = author_info.get("birth_date")
            death_date = author_info.get("death_date")
            website = author_info.get("website")
            bio = author_info.get("bio")
            
            # Get user info if available
            user_id = None
            user_info = author_info.get("user", {})
            if user_info:
                user_id = user_info.get("id")
                # Add user to database if it doesn't exist
                if user_id:
                    try:
                        self.db_manager.users.add(user_info)
                    except Exception as e:
                        logger.log_warning(f"Error adding user {user_id}: {str(e)}")
            
            # Validate database manager
            if not self.db_manager:
                raise RuntimeError("Database manager is not initialized")
            
            try:
                # Check if author already exists in database
                existing_authors = self.db_manager.execute_query(
                    "SELECT id FROM authors WHERE author_name = ?", 
                    (author_name,)
                )
                
                author_data = {
                    'id': api_author_id,
                    'userId': user_id,
                    'author_name': author_name,
                    'author_image_url': author_image_url,
                    'birth_date': birth_date,
                    'death_date': death_date,
                    'website': website,
                    'bio': bio
                }
                
                local_id = None
                
                if existing_authors:
                    # Update existing author
                    local_id = existing_authors[0][0]
                    if not self.db_manager.authors.update(local_id, author_data):
                        raise DatabaseError(f"Failed to update author with ID {local_id}")
                else:
                    # Insert new author
                    local_id = self.db_manager.authors.add(author_data)
                    if not local_id:
                        raise DatabaseError("Failed to add new author to database")
                        
                    # Store the mapping between API ID and local ID
                    if not self.db_manager.settings.set(f"author_api_id_{api_author_id}", str(local_id)):
                        logger.log_warning(f"Failed to store mapping for author ID {api_author_id}")
                
                # Download author image if URL is provided
                if author_image_url and local_id:
                    # Get image processor from synchronizer
                    image_processor = self.synchronizer.image_processor
                    
                    try:
                        if not image_processor.download_author_image(local_id, author_image_url):
                            logger.log_warning(f"Failed to download image from {author_image_url}")
                    except requests.RequestException as e:
                        logger.log_error(f"Network error downloading author image: {e}")
                    except IOError as e:
                        logger.log_error(f"IO error saving author image: {e}")
                
                return local_id
                
            except (sqlite3.Error, sqlite3.DatabaseError) as db_error:
                logger.log_error(f"Database error: {db_error}")
                raise DatabaseError(f"Error accessing database: {db_error}")
                
        except Exception as e:
            logger.log_error(f"Unexpected error processing author '{author_info.get('author_name', 'unknown')}': {e}")
            raise AuthorProcessingError(f"Failed to process author: {e}")

