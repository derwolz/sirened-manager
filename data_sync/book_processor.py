"""
Book data processing functionality.
"""

import json
import sqlite3
import app_logger as logger
from exceptions import DatabaseError

class BookProcessor:
    """
    Handles processing and storing book data
    """
    def __init__(self, db_manager, synchronizer):
        self.db_manager = db_manager
        self.synchronizer = synchronizer
        
    def process_book(self, book, author_id):
        """Process and store book data in the database"""
        try:
            if not book:
                raise ValueError("Book data cannot be None or empty")
            
            # Validate required fields
            if not book.get("title"):
                raise ValueError("Book must have a title")
            
            # Extract book data
            db_book = {
                "id": book.get("id"),
                "title": book.get("title", ""),
                "description": book.get("description", ""),
                "pageCount": book.get("pageCount", 0),
                "publishedDate": book.get("publishedDate"),
                "isbn": book.get("isbn"),
                "authorId": book.get("authorId", 0),
                "author": book.get("authorName", book.get("author", "")),
                "authorImageUrl": book.get("authorImageUrl", ""),
                "promoted": book.get("promoted") if book.get("promoted") is not None else False,
                "awards": book.get("awards", ""),
                "setting": book.get("setting", ''),
                "formats": book.get("formats", []),
                "originalTitle": book.get("originalTitle", ''),
                "series": book.get("series", ''),
                "characters": book.get("characters", []),
                "asin": book.get('asin'),
                "language": book.get('language', ''),
                "referralLinks": book.get("referralLinks", []),
                "impressionCount": book.get("impressionCount", 0),
                "clickThroughCount": book.get("clickThroughCount", 0),
                "lastImpressionAt": book.get("lastImpressionAt"),
                "lastClickThroughAt": book.get("lastClickThroughAt"),
                "internal_details": book.get('internal_details', {}),
            }
            
            # Convert complex objects to JSON strings
            for key, value in db_book.items():
                try:
                    if isinstance(value, (list, dict)):
                        db_book[key] = json.dumps(value)
                except TypeError as e:
                    logger.log_error(f"Error converting value for {key}: {e}")
                    db_book[key] = str(value) if value is not None else ""
            
            try:
                # Check if book already exists in database
                existing_books = self.db_manager.execute_query(
                    "SELECT id FROM books WHERE id = ? OR (title = ? AND authorId = ?)", 
                    (db_book["id"], db_book["title"], db_book["authorId"])
                )
                
                if not self.db_manager:
                    raise RuntimeError("Database manager is not initialized")
                    
                if existing_books:
                    # Update existing book
                    local_id = existing_books[0][0]
                    if not self.db_manager.books.update_book(local_id, db_book):
                        raise RuntimeError(f"Failed to update existing book with ID {local_id}")
                    return local_id
                else:
                    # Insert new book
                    local_id = self.db_manager.books.add(db_book)
                    
                    if not local_id:
                        raise RuntimeError("Failed to add new book to database")
                    
                    # Store the mapping between API ID and local ID
                    if db_book["id"]:
                        self.db_manager.settings.set(f"book_api_id_{db_book['id']}", str(local_id))
                    return local_id
                    
            except (sqlite3.Error, sqlite3.DatabaseError) as db_error:
                logger.log_error(f"Database error: {db_error}")
                raise DatabaseError(f"Error accessing database: {db_error}")
                
        except json.JSONDecodeError as json_error:
            logger.log_error(f"JSON encoding error: {json_error}")
            raise
        except Exception as e:
            logger.log_error(f"Unexpected error processing book '{book.get('title', 'unknown')}': {e}")
            raise Exception(f"Failed to process book: {e}")

