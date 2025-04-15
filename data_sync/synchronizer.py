"""
Main DataSynchronizer class that orchestrates the synchronization process.
"""

import json
import requests
from datetime import datetime
from config import API_BASE_URL, AUTHORS_ENDPOINT, PUBLISHER_AUTHORS_ENDPOINT, GENRE_ENDPOINT
import app_logger as logger
from .author_processor import AuthorProcessor
from .book_processor import BookProcessor
from .genre_processor import GenreProcessor
from .image_processor import ImageProcessor
from exceptions import DatabaseError

class DataSynchronizer:
    """
    Synchronizes data between the API and local database
    """
    def __init__(self, db_manager, parent=None):
        self.db_manager = db_manager
        self.parent = parent
        self.api_base_url = API_BASE_URL
        
        # Initialize processors
        self.author_processor = AuthorProcessor(db_manager, self)
        self.book_processor = BookProcessor(db_manager, self)
        self.genre_processor = GenreProcessor(db_manager)
        self.image_processor = ImageProcessor(db_manager)
        
    def synchronize_data(self, cookies=None):
        """Main method to synchronize all data from the API to local database"""
        if not cookies:
            if self.parent and hasattr(self.parent, 'cookies'):
                cookies = self.parent.cookies
            else:
                raise ValueError("No cookies provided for authentication")
        
        # Check if user is a publisher
        is_publisher = False
        if self.parent and hasattr(self.parent, 'is_publisher'):
            is_publisher = self.parent.is_publisher.get()
        
        # Pull data based on user role
        if is_publisher:
            self.sync_publisher_data(cookies)
        else:
            self.sync_author_data(cookies)
        
        # Always sync genres for both user types
        self.genre_processor.sync_genres(cookies)
        
        # Download all images
        self.image_processor.download_all_images()
            
        # Update UI if parent reference exists
        if self.parent:
            self.update_parent_data()
            
        return True
    
    def make_api_request(self, endpoint, cookies):
        """Make a GET request to the API with authentication cookies"""
        url = f"{self.api_base_url}{endpoint}"
        return requests.get(url, cookies=cookies)
        
    def sync_publisher_data(self, cookies):
        """Sync data for publisher users"""
        try:
            # Fetch publisher catalogue data
            response = self.make_api_request(PUBLISHER_AUTHORS_ENDPOINT, cookies)
      
            if response.status_code != 200:
                logger.log_error(f"Failed to fetch publisher data: {response.status_code}")
                return False
            
            publisher_data = response.json()
            
            # Process each publisher in the data
            for publisher_entry in publisher_data:
                publisher_info = publisher_entry.get("publisher", {})
                catalogue = publisher_entry.get("catalogue", [])
                
                # Store publisher info in settings
                self.store_publisher_info(publisher_info)
                
                # Process authors and books in the catalogue
                for author_entry in catalogue:
                    author_info = author_entry.get("author", {})
                    books = author_entry.get("books", [])
                    
                    # Process author data
                    author_id = self.author_processor.process_author(author_info)
                    
                    # Process books for this author
                    for book in books:
                        # Ensure the book is associated with the correct author
                        book["authorId"] = author_info.get("id")
                        book["author"] = author_info.get("author_name")
                        book["authorImageUrl"] = author_info.get("author_image_url")
                        
                        book_id = self.book_processor.process_book(book, author_id)
                        
                        # Process images if any
                        if "images" in book and book["images"]:
                            self.image_processor.process_book_images(book["images"], book["id"])
                        
                        # Process genres if any
                        if "genres" in book and book["genres"]:
                            self.genre_processor.process_book_genres(book["genres"], book_id)
            
            return True
            
        except Exception as e:
            logger.log_error(f"Error syncing publisher data: {str(e)}")
            return False
            
    def sync_author_data(self, cookies):
        """Sync data for author or regular users"""
        try:
            # Fetch author data
            response = self.make_api_request(AUTHORS_ENDPOINT, cookies)
            
            if response.status_code != 200:
                logger.log_error(f"Failed to fetch author data: {response.status_code}")
                return False
            
            author_data = response.json()
            
            # Process each author in the data
            for author_entry in author_data:
                author_info = author_entry.get("author", {})
                books = author_entry.get("books", [])
                
                # Process author data
                author_id = self.author_processor.process_author(author_info)
                
                # Process books for this author
                for book in books:
                    # Ensure the book is associated with the correct author
                    book["authorId"] = author_info.get("id")
                    book["author"] = author_info.get("author_name")
                    book["authorImageUrl"] = author_info.get("author_image_url")
                    
                    book_id = self.book_processor.process_book(book, author_id)
                    
                    # Process images if any
                    if "images" in book and book["images"]:
                        self.image_processor.process_book_images(book["images"], book["id"])
                    
                    # Process genres if any
                    if "genres" in book and book["genres"]:
                        self.genre_processor.process_book_genres(book["genres"], book_id)
            
            return True
            
        except Exception as e:
            logger.log_error(f"Error syncing author data: {str(e)}")
            return False
    
    def store_publisher_info(self, publisher_info):
        """Store publisher information in the settings table"""
        if not publisher_info:
            return
            
        publisher_id = publisher_info.get("id")
        publisher_name = publisher_info.get("name", "")
        publisher_description = publisher_info.get("publisher_description", "")
        business_email = publisher_info.get("business_email", "")
        website = publisher_info.get("website", "")
        
        # Store relevant publisher details in settings
        self.db_manager.set_setting("publisher_id", str(publisher_id))
        self.db_manager.set_setting("publisher_name", publisher_name)
        self.db_manager.set_setting("publisher_description", publisher_description)
        self.db_manager.set_setting("publisher_email", business_email)
        self.db_manager.set_setting("publisher_website", website)
        
        # Mark user as a publisher
        self.db_manager.set_setting("is_publisher", "1")
    
    def update_parent_data(self):
        """Update parent application's data structures with fresh database data"""
        if not self.parent:
            return
        
        # Load authors
        authors = []
        authors_raw = self.db_manager.authors.get_all()  # Changed from get_authors()
        for author_row in authors_raw:
            author = {
                "id": author_row[0],
                "author_name": author_row[2],
                "author_image_url": author_row[3],
                "birth_date": author_row[4],
                "death_date": author_row[5],
                "website": author_row[6],
                "bio": author_row[7]
            }
            authors.append(author)        
        # Load books
        books = []
        books_raw = self.db_manager.books.get_all()
        for book_row in books_raw:
            # Try to parse internal_details if available
            internal_details = {}
            if book_row[24] and book_row[24].strip():
                try:
                    internal_details = json.loads(book_row[24])
                except:
                    logger.log_error(f"Failed to parse internal_details: {book_row[24]}")
            
            # Extract formats as list if available
            formats = []
            if book_row[8]:
                try:
                    formats = json.loads(book_row[8])
                except:
                    formats = book_row[8].split(",") if "," in book_row[8] else [book_row[8]]
            
            # Extract characters as list if available
            characters = []
            if book_row[14]:
                try:
                    characters = json.loads(book_row[14])
                except:
                    characters = book_row[14].split(",") if "," in book_row[14] else [book_row[14]]
            
            # Extract referral links as list if available
            referral_links = []
            if book_row[18]:
                try:
                    referral_links = json.loads(book_row[18])
                except:
                    referral_links = book_row[18].split(",") if "," in book_row[18] else [book_row[18]]
                    
            # Build the book object based on table structure
            book = {
                "id": book_row[0],
                "title": book_row[1],
                "author": book_row[2] if book_row[2] else "",
                "author_id": book_row[3] if book_row[3] else None,
                "description": book_row[4] if book_row[4] else "",
                "author_image_url": book_row[5] if book_row[5] else "",
                "promoted": bool(book_row[6]) if book_row[6] is not None else False,
                "page_count": book_row[7] if book_row[7] else 0,
                "formats": formats,
                "publish_date": book_row[9],
                "awards": book_row[10] if book_row[10] else "",
                "original_title": book_row[11] if book_row[11] else "",
                "series": book_row[12] if book_row[12] else "",
                "setting": book_row[13] if book_row[13] else "",
                "characters": characters,
                "isbn": book_row[15] if book_row[15] else "",
                "asin": book_row[16] if book_row[16] else "",
                "language": book_row[17] if book_row[17] else "",
                "referral_links": referral_links,
                "impression_count": book_row[19] if book_row[19] else 0,
                "click_through_count": book_row[20] if book_row[20] else 0,
                "last_impression_at": book_row[21],
                "last_click_through_at": book_row[22],
                "internal_details": internal_details,
            }

            books.append(book)
        
        # Load genres
        genres = []
        genres_raw = self.db_manager.genres.get_all()
        for genre_row in genres_raw:
            genre = {
                "id": genre_row[0],
                "name": genre_row[1],
                "description": genre_row[2],
                "type": genre_row[3],
                "parentId": genre_row[4]
            }
            genres.append(genre)
        
        # Update parent data
        self.parent.authors = authors
        self.parent.books = books
        self.parent.genres = genres
        
        # Refresh UI if methods exist
        if hasattr(self.parent, 'authors_tab') and hasattr(self.parent.authors_tab, 'update_authors_listbox'):
            self.parent.authors_tab.update_authors_listbox()
        
        if hasattr(self.parent, 'books_tab') and hasattr(self.parent.books_tab, 'update_books_listbox'):
            self.parent.books_tab.update_books_listbox()
            
        if hasattr(self.parent, 'books_tab') and hasattr(self.parent.books_tab, 'update_book_author_dropdown'):
            self.parent.books_tab.update_book_author_dropdown()
        
        if hasattr(self.parent, 'genres_tab') and hasattr(self.parent.genres_tab, 'update_genres_tree'):
            self.parent.genres_tab.update_genres_tree()
            
        if hasattr(self.parent, 'genres_tab') and hasattr(self.parent.genres_tab, 'update_genre_book_dropdown'):
            self.parent.genres_tab.update_genre_book_dropdown()
            
        if hasattr(self.parent, 'images_tab') and hasattr(self.parent.images_tab, 'update_image_item_dropdown'):
            self.parent.images_tab.update_image_item_dropdown()

