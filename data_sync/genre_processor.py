"""
Genre data processing functionality.
"""

import json
from datetime import datetime
import app_logger as logger
from config import GENRE_ENDPOINT

class GenreProcessor:
    """
    Handles processing and storing genre data
    """
    def __init__(self, db_manager, synchronizer=None):
        self.db_manager = db_manager
        self.synchronizer = synchronizer
        
    def sync_genres(self, cookies=None):
        """Sync genre data from the API or import from provided format"""
        try:
            # Try to fetch genres from API first
            if cookies and hasattr(self, 'synchronizer'):
                response = self.synchronizer.make_api_request(GENRE_ENDPOINT, cookies)
                
                if response.status_code == 200:
                    genres_data = response.json()
                    self.import_genres(genres_data)
                    return True
                else:
                    logger.log_error("unable to fetch genre data")
            # If API fetch fails or no cookies, check if we have cached genres
            cached_genres = self.db_manager.settings.get("cached_genres")
            if cached_genres:
                genres_data = json.loads(cached_genres)
                self.import_genres(genres_data)
                return True
                
            return False
            
        except Exception as e:
            logger.log_error(f"Error syncing genres: {str(e)}")
            return False
    
    def import_genres(self, genres_data):
        """Import genres from the provided data structure"""
        if not genres_data:
            logger.log_debug(f"give me something you piece of shit I'm so sick of stupid html responses")
            return False
        logger.log_debug(f"importing genres: {genres_data}") 
        try:
            # Process each genre
            for genre in genres_data:
                # Add the genre to the database
                self.db_manager.genres.add(genre)
                
            # Cache the genres data for offline use
            self.db_manager.settings.set("cached_genres", json.dumps(genres_data))
            self.db_manager.settings.set("genres_last_updated", datetime.now().isoformat())
            
            return True
            
        except Exception as e:
            logger.log_error(f"Error importing genres: {str(e)}")
            return False
    
    def import_genres_from_json(self, json_data):
        """Import genres from a JSON string or object"""
        try:
            # Parse JSON if it's a string
            if isinstance(json_data, str):
                genres_data = json.loads(json_data)
            else:
                genres_data = json_data
                
            # Import the genres
            result = self.import_genres(genres_data)
            
            # Update UI if needed
            if hasattr(self, 'parent') and self.parent and hasattr(self.parent, 'genres_tab') and hasattr(self.parent.genres_tab, 'update_genres_tree'):
                self.parent.genres_tab.update_genres_tree()
                
            return result
            
        except Exception as e:
            logger.log_error(f"Error importing genres from JSON: {str(e)}")
            return False
    
    def process_book_genres(self, genres, book_id):
        """Process and store book genre associations"""
        if not genres or not book_id:
            return
            
        # Clear existing genre associations for this book
        self.db_manager.execute_query(
            "DELETE FROM book_genres WHERE book_id = ?", 
            (book_id,)
        )
        
        # Add new genre associations
        for genre in genres:
            genre_id = genre.get("id")
            if genre_id:
                self.db_manager.books.add_genre(book_id, genre_id)

