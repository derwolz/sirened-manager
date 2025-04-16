"""
Taxonomy data processing functionality.
"""

import json
from datetime import datetime
import app_logger as logger
from exceptions import InvalidDataError, DatabaseError

class TaxonomyProcessor:
    """
    Handles processing and storing taxonomy data (genres, subgenres, themes, tropes, etc.)
    """
    def __init__(self, db_manager, synchronizer):
        self.db_manager = db_manager
        self.synchronizer = synchronizer
        
    def process_book_taxonomies(self, taxonomies, book_id):
        """Process and store book taxonomy associations"""
        if not taxonomies or not book_id:
            logger.log_warning(f"No taxonomies provided for book ID {book_id}")
            return False
        
        try:
            # First, ensure we have the local book ID
            local_book_id = book_id
            if isinstance(book_id, str) and book_id.isdigit():
                local_book_id = int(book_id)
            
            # Clear existing taxonomy associations for this book
            self.db_manager.execute_query(
                "DELETE FROM book_genres WHERE book_id = ?", 
                (local_book_id,)
            )
            
            # Add each taxonomy item to the database if it doesn't exist
            # and create the association with the book
            for taxonomy in taxonomies:
                taxonomy_id = taxonomy.get("taxonomyId")
                if not taxonomy_id:
                    logger.log_warning(f"Taxonomy without ID found for book {local_book_id}")
                    continue
                
                # Check if taxonomy exists, if not add it
                existing_taxonomy = self.db_manager.execute_query(
                    "SELECT id FROM genres WHERE id = ?", 
                    (taxonomy_id,)
                )
                
                # If taxonomy doesn't exist, add it
                if not existing_taxonomy:
                    taxonomy_data = {
                        'id': taxonomy_id,
                        'name': taxonomy.get("name", ""),
                        'description': taxonomy.get("description", ""),
                        'type': taxonomy.get("type", "genre"),
                        'parentId': None  # Parent relationship would need to be determined separately
                    }
                    
                    try:
                        self.db_manager.genres.add(taxonomy_data)
                        logger.log_debug(f"Added new taxonomy: {taxonomy.get('name')}")
                    except Exception as e:
                        logger.log_error(f"Error adding taxonomy {taxonomy_id}: {str(e)}")
                        continue
                
                # Create the book-taxonomy relationship with rank and importance
                try:
                    query = """
                    INSERT INTO book_genres (book_id, genre_id, rank, importance) 
                    VALUES (?, ?, ?, ?)
                    """
                    params = (
                        local_book_id, 
                        taxonomy_id, 
                        taxonomy.get("rank", 0),
                        taxonomy.get("importance", 0.0)
                    )
                    
                    self.db_manager.execute_query(query, params)
                    
                except Exception as e:
                    logger.log_error(f"Error associating taxonomy {taxonomy_id} with book {local_book_id}: {str(e)}")
            
            return True
            
        except Exception as e:
            logger.log_error(f"Unexpected error processing taxonomies for book {book_id}: {str(e)}")
            return False
    
    def get_book_taxonomies(self, book_id):
        """Get all taxonomies associated with a book with their rank and importance"""
        query = """
        SELECT g.id, g.name, g.description, g.type, bg.rank, bg.importance
        FROM genres g
        JOIN book_genres bg ON g.id = bg.genre_id
        WHERE bg.book_id = ?
        ORDER BY bg.rank
        """
        
        return self.db_manager.execute_query(query, (book_id,))
