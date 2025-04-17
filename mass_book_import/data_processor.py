# book_import/data_processor.py

import re
import json
from datetime import datetime
import app_logger as logger
from exceptions import DatabaseError

class DataProcessor:
    """Processes data for book imports"""
    
    def __init__(self, parent):
        self.parent = parent
        self.db_manager = parent.db_manager if hasattr(parent, 'db_manager') else None
        
    def load_and_transform_data(self, file_path, file_format, skip_header, mapping_vars):
        """Load data from file and transform according to mapping"""
        try:
            # Load raw data from file handler
            from .file_handlers import FileHandler
            file_handler = FileHandler()
            raw_data = file_handler.read_file_data(file_path, file_format, skip_header)
            
            if not raw_data:
                return []
            
            # Transform data according to mapping
            transformed_data = []
            for row in raw_data:
                book_data = {}
                
                for file_field, mapping_var in mapping_vars.items():
                    book_field = mapping_var.get()
                    
                    if book_field and file_field in row:
                        value = row[file_field]
                        
                        # Handle special transformations
                        if book_field == "formats":
                            value = self._transform_formats(value)
                        
                        elif book_field == "page_count":
                            value = self._transform_page_count(value)
                        
                        elif book_field == "characters":
                            value = self._transform_characters(value)
                        
                        elif book_field == "publish_date":
                            value = self._transform_publish_date(value)
                        
                        book_data[book_field] = value
                
                # Add required fields if missing
                if "title" not in book_data or not book_data["title"]:
                    continue  # Skip books without title
                
                if "author" not in book_data or not book_data["author"]:
                    continue  # Skip books without author
                
                if "description" not in book_data or not book_data["description"]:
                    book_data["description"] = "No description provided."
                
                if "language" not in book_data or not book_data["language"]:
                    book_data["language"] = "English"
                
                if "formats" not in book_data or not book_data["formats"]:
                    book_data["formats"] = ["digital"]
                
                if "page_count" not in book_data:
                    book_data["page_count"] = 1
                
                if "publish_date" not in book_data:
                    book_data["publish_date"] = datetime.now().strftime("%Y-%m-%d")
                
                if "characters" not in book_data:
                    book_data["characters"] = []
                
                transformed_data.append(book_data)
            
            return transformed_data
            
        except Exception as e:
            logger.log_error(f"Error loading and transforming data: {str(e)}")
            raise
    
    def _transform_formats(self, value):
        """Transform formats field value"""
        if isinstance(value, str):
            return [v.strip().lower() for v in value.split(',')]
        elif isinstance(value, (int, float, bool)):
            return [str(value).lower()]
        elif isinstance(value, list):
            return value
        return ["digital"]  # Default to digital if empty
    
    def _transform_page_count(self, value):
        """Transform page count field value"""
        try:
            value = int(value)
            if value <= 0:
                value = 1
        except (ValueError, TypeError):
            value = 1
        return value
    
    def _transform_characters(self, value):
        """Transform characters field value"""
        if isinstance(value, str):
            return [v.strip() for v in value.split(',') if v.strip()]
        elif isinstance(value, list):
            return value
        return []
    
    def _transform_publish_date(self, value):
        """Transform publish date field value"""
        if value and isinstance(value, str) and not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
            try:
                # Try common date formats
                for fmt in ["%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%m-%d-%Y", "%d-%m-%Y"]:
                    try:
                        parsed_date = datetime.strptime(value, fmt)
                        value = parsed_date.strftime("%Y-%m-%d")
                        break
                    except ValueError:
                        continue
            except Exception:
                # If all parsing attempts fail, use current date
                value = datetime.now().strftime("%Y-%m-%d")
        
        # If still not in the right format, default to current date
        if not isinstance(value, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", str(value)):
            value = datetime.now().strftime("%Y-%m-%d")
            
        return value
    
    def validate_import_data(self, data, update_existing=True):
        """Validate the data to be imported"""
        validation_issues = []
        
        for i, book in enumerate(data):
            book_num = i + 1
            
            # Check for missing required fields
            if not book.get("title"):
                validation_issues.append(f"Book #{book_num}: Missing title")
            
            if not book.get("author"):
                validation_issues.append(f"Book #{book_num}: Missing author")
            
            # Validate date format
            publish_date = book.get("publish_date")
            if publish_date and not re.match(r"^\d{4}-\d{2}-\d{2}$", str(publish_date)):
                validation_issues.append(f"Book #{book_num}: Invalid publish date format for '{book.get('title')}' - expected YYYY-MM-DD")
            
            # Validate page count
            page_count = book.get("page_count")
            if page_count is not None:
                try:
                    page_count = int(page_count)
                    if page_count <= 0:
                        validation_issues.append(f"Book #{book_num}: Invalid page count for '{book.get('title')}' - must be positive")
                except (ValueError, TypeError):
                    validation_issues.append(f"Book #{book_num}: Invalid page count for '{book.get('title')}' - must be a number")
            
            # Check if book already exists in database
            if hasattr(self, 'db_manager') and self.db_manager:
                existing_books = self.db_manager.execute_query(
                    "SELECT id FROM books WHERE title = ? AND author = ?", 
                    (book.get("title"), book.get("author"))
                )
                
                if existing_books and not update_existing:
                    validation_issues.append(f"Book #{book_num}: '{book.get('title')}' by {book.get('author')} already exists and update option is disabled")
        
        return validation_issues
    
    def import_books(self, data, update_existing=True, progress_callback=None):
        """Process the actual import of books"""
        try:
            # Initialize counters
            total_books = len(data)
            books_added = 0
            books_updated = 0
            books_skipped = 0
            current_book = 0
            
            for book in data:
                current_book += 1
                if progress_callback:
                    progress_callback(current_book, total_books)
                
                # Check if book already exists
                title = book.get("title", "").strip()
                author = book.get("author", "").strip()
                
                if not title or not author:
                    books_skipped += 1
                    continue
                
                # Try to find author ID in database
                author_id = None
                if hasattr(self, 'db_manager') and self.db_manager:
                    try:
                        author_results = self.db_manager.execute_query(
                            "SELECT id FROM authors WHERE author_name = ?", 
                            (author,)
                        )
                        
                        if author_results:
                            author_id = author_results[0][0]
                        else:
                            # Author doesn't exist, create it
                            author_data = {
                                "author_name": author,
                                "bio": f"Author of {title}"
                            }
                            
                            author_id = self.db_manager.authors.add(author_data)
                            logger.log_debug(f"Created new author: {author} with ID {author_id}")
                    except Exception as e:
                        logger.log_error(f"Error checking author: {str(e)}")
                
                # Process formats
                formats = book.get("formats", ["digital"])
                if isinstance(formats, str):
                    formats = [f.strip().lower() for f in formats.split(',') if f.strip()]
                
                # Process characters
                characters = book.get("characters", [])
                if isinstance(characters, str):
                    characters = [c.strip() for c in characters.split(',') if c.strip()]
                
                # Prepare book data
                book_data = {
                    "title": title,
                    "author": author,
                    "author_id": author_id,
                    "description": book.get("description", "No description provided."),
                    "internal_details": book.get("internal_details", ""),
                    "pageCount": book.get("page_count", 1),
                    "formats": formats,
                    "publishedDate": book.get("publish_date", datetime.now().strftime("%Y-%m-%d")),
                    "awards": book.get("awards", ""),
                    "series": book.get("series", ""),
                    "setting": book.get("setting", ""),
                    "characters": characters,
                    "language": book.get("language", "English"),
                    "referral_links": book.get("referral_links", ""),
                    "isbn": book.get("isbn", ""),
                    "asin": book.get("asin", "")
                }
                
                # Check if book already exists
                book_index = None
                book_id = None
                
                if hasattr(self, 'db_manager') and self.db_manager:
                    try:
                        existing_books = self.db_manager.execute_query(
                            "SELECT id FROM books WHERE title = ? AND (author = ? OR authorId = ?)", 
                            (title, author, author_id)
                        )
                        
                        if existing_books:
                            book_id = existing_books[0][0]
                            
                            if update_existing:
                                # Update existing book in database
                                self.db_manager.books.update(book_id, book_data)
                                books_updated += 1
                                logger.log_debug(f"Updated book: {title} with ID {book_id}")
                            else:
                                # Skip this book
                                books_skipped += 1
                                continue
                        else:
                            # Add new book to database
                            book_id = self.db_manager.books.add(book_data)
                            books_added += 1
                            logger.log_debug(f"Added book: {title} with ID {book_id}")
                    except Exception as e:
                        logger.log_error(f"Error adding/updating book in database: {str(e)}")
                        books_skipped += 1
                        continue
                else:
                    # Check in-memory data if no database
                    for i, existing_book in enumerate(self.parent.books):
                        if isinstance(existing_book, dict) and existing_book.get("title") == title:
                            book_index = i
                            break
                    
                    if book_index is not None:
                        if update_existing:
                            # Update existing book in memory
                            self.parent.books[book_index] = book_data
                            books_updated += 1
                        else:
                            # Skip this book
                            books_skipped += 1
                            continue
                    else:
                        # Add new book to memory
                        self.parent.books.append(book_data)
                        books_added += 1
            
            return {
                'added': books_added,
                'updated': books_updated,
                'skipped': books_skipped,
                'total': total_books
            }
            
        except Exception as e:
            logger.log_error(f"Error importing books: {str(e)}")
            raise
