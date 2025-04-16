"""
Specialized synchronization utilities for pushing data to the server.
"""
import json
import tkinter as tk
from tkinter import messagebox
import requests
import threading
import app_logger as logger
from config import (
    API_BASE_URL, 
    UPLOAD_AUTHOR_ENDPOINT, 
    UPLOAD_BOOK_ENDPOINT
)

class DataPushSynchronizer:
    """Handles pushing local data to the server"""
    
    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db_manager = db_manager
        self.cookies = None
        self.is_syncing = False
        self.sync_lock = threading.Lock()
        
    def set_auth_cookies(self, cookies):
        """Set authentication cookies for API requests"""
        self.cookies = cookies
        
    def push_all_data(self):
        """
        Push all authors and books to the server
        Returns True if successful, False otherwise
        """
        if not self.cookies:
            logger.log_error("No authentication cookies provided")
            self._show_error("Authentication Required", "Please log in first")
            return False
            
        # Acquire lock to prevent concurrent modifications
        with self.sync_lock:
            if self.is_syncing:
                logger.log_warning("Sync already in progress")
                return False
                
            self.is_syncing = True
            
        try:
            # Lock UI
            self._toggle_ui_lock(True)
            
            # Push authors first
            authors_result = self.push_authors()
            if not authors_result:
                logger.log_error("Failed to push authors")
                return False
                
            # Push books
            books_result = self.push_books()
            if not books_result:
                logger.log_error("Failed to push books")
                return False
                
            # If everything succeeded, pull the latest data
            if authors_result and books_result:
                sync_result = self._sync_from_server()
                if sync_result:
                    self._show_success("Sync Completed", "All data successfully synchronized with the server")
                return sync_result
                
            return False
            
        except Exception as e:
            logger.log_error(f"Error during data push: {str(e)}")
            self._show_error("Sync Error", f"An unexpected error occurred: {str(e)}")
            return False
            
        finally:
            # Always release the lock and unlock UI
            self.is_syncing = False
            self._toggle_ui_lock(False)
    
    def push_authors(self):
        """Push all authors to the server"""
        try:
            # Get all authors from database
            authors = self.db_manager.authors.get_all()
            
            success_count = 0
            total_count = len(authors)
            
            for author in authors:
                # Format author data for API
                author_data = {
                    'id': author[0],
                    'userId': author[1],
                    'author_name': author[2],
                    'author_image_url': author[3],
                    'birth_date': author[4],
                    'death_date': author[5],
                    'website': author[6],
                    'bio': author[7]
                }
                
                # Send the author data to server
                response = self._make_api_request(
                    "POST", 
                    f"{UPLOAD_AUTHOR_ENDPOINT}", 
                    data=author_data
                )
                
                if response and response.status_code in (200, 201):
                    success_count += 1
                    logger.log_debug(f"Successfully pushed author: {author_data['author_name']}")
                else:
                    # Handle error
                    error_msg = "Unknown error"
                    if response:
                        try:
                            error_data = response.json()
                            error_msg = error_data.get("message", f"Error {response.status_code}")
                            status = error_data.get("status", "Error")
                            
                            error_display = f"Failed to upload author: {author_data['author_name']}\n"
                            error_display += f"Message: {error_msg}\n"
                            error_display += f"Status: {status}"
                            
                            self._show_error("Author Upload Failed", error_display)
                        except:
                            self._show_error("Author Upload Failed", 
                                            f"Failed to upload author: {author_data['author_name']}\n"
                                            f"Status code: {response.status_code}")
                    else:
                        self._show_error("Author Upload Failed", 
                                        f"Failed to upload author: {author_data['author_name']}\n"
                                        "No response from server")
                    
                    logger.log_error(f"Failed to push author {author_data['author_name']}: {error_msg}")
            
            logger.log_debug(f"Author push completed: {success_count}/{total_count} successful")
            return success_count == total_count
            
        except Exception as e:
            logger.log_error(f"Error pushing authors: {str(e)}")
            self._show_error("Author Push Error", f"An unexpected error occurred: {str(e)}")
            return False
    
    def push_books(self):
        """Push all books to the server"""
        try:
            # Get all books from database
            books = self.db_manager.books.get_all()
            
            success_count = 0
            total_count = len(books)
            
            for book in books:
                # Format book data for API
                book_data = {
                    'id': book[0],
                    'title': book[1],
                    'authorId': book[3],  # AuthorId is at index 3
                    'description': book[4],
                    'promoted': bool(book[6]),
                    'pageCount': book[7],
                    'formats': self._parse_json_field(book[8]),
                    'publishedDate': book[9],
                    'awards': self._parse_json_field(book[10]),
                    'originalTitle': book[11],
                    'series': book[12],
                    'setting': book[13],
                    'characters': self._parse_json_field(book[14]),
                    'isbn': book[15],
                    'asin': book[16],
                    'language': book[17],
                    'referralLinks': self._parse_json_field(book[18])
                }
                
                # Get genre taxonomies for this book
                taxonomies = self.db_manager.execute_query(
                    """
                    SELECT g.id as taxonomyId, bg.rank, bg.importance, g.name, g.type, g.description
                    FROM book_genres bg
                    JOIN genres g ON bg.genre_id = g.id
                    WHERE bg.book_id = ?
                    ORDER BY bg.rank
                    """,
                    (book[0],)
                )
                
                # Format taxonomies
                genre_taxonomies = []
                for tax in taxonomies:
                    taxonomy = {
                        'taxonomyId': tax[0],
                        'rank': tax[1],
                        'importance': tax[2],
                        'name': tax[3],
                        'type': tax[4],
                        'description': tax[5]
                    }
                    genre_taxonomies.append(taxonomy)
                
                book_data['genreTaxonomies'] = genre_taxonomies
                
                # Send the book data to server
                response = self._make_api_request(
                    "POST", 
                    f"{UPLOAD_BOOK_ENDPOINT}", 
                    data=book_data
                )
                
                if response and response.status_code in (200, 201):
                    success_count += 1
                    logger.log_debug(f"Successfully pushed book: {book_data['title']}")
                else:
                    # Handle error
                    error_msg = "Unknown error"
                    if response:
                        try:
                            error_data = response.json()
                            error_msg = error_data.get("message", f"Error {response.status_code}")
                            status = error_data.get("status", "Error")
                            
                            error_display = f"Failed to upload book: {book_data['title']}\n"
                            error_display += f"Message: {error_msg}\n"
                            error_display += f"Status: {status}"
                            
                            self._show_error("Book Upload Failed", error_display)
                        except:
                            self._show_error("Book Upload Failed", 
                                            f"Failed to upload book: {book_data['title']}\n"
                                            f"Status code: {response.status_code}")
                    else:
                        self._show_error("Book Upload Failed", 
                                        f"Failed to upload book: {book_data['title']}\n"
                                        "No response from server")
                    
                    logger.log_error(f"Failed to push book {book_data['title']}: {error_msg}")
            
            logger.log_debug(f"Book push completed: {success_count}/{total_count} successful")
            return success_count == total_count
            
        except Exception as e:
            logger.log_error(f"Error pushing books: {str(e)}")
            self._show_error("Book Push Error", f"An unexpected error occurred: {str(e)}")
            return False
    
    def _parse_json_field(self, field_value):
        """Parse a JSON field from the database"""
        if not field_value:
            return []
            
        try:
            if isinstance(field_value, str):
                return json.loads(field_value)
            return field_value
        except json.JSONDecodeError:
            # If it's a comma-separated list, convert to list
            if isinstance(field_value, str) and "," in field_value:
                return field_value.split(",")
            return [field_value] if field_value else []
    
    def _make_api_request(self, method, endpoint, data=None):
        """Make an API request with proper error handling"""
        url = f"{API_BASE_URL}{endpoint}"
        
        try:
            logger.log_debug(f"Making {method} request to {url}")
            
            if method.upper() == "GET":
                return requests.get(url, cookies=self.cookies)
            elif method.upper() == "POST":
                return requests.post(url, json=data, cookies=self.cookies)
            elif method.upper() == "PUT":
                return requests.put(url, json=data, cookies=self.cookies)
            elif method.upper() == "DELETE":
                return requests.delete(url, cookies=self.cookies)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
        except requests.RequestException as e:
            logger.log_error(f"API Request error: {str(e)}")
            return None
    
    def _sync_from_server(self):
        """Pull the latest data from server after pushing"""
        try:
            # Use the existing DataSynchronizer to pull from server
            synchronizer = self.parent.synchronizer
            if synchronizer:
                return synchronizer.synchronize_data(self.cookies)
            return False
        except Exception as e:
            logger.log_error(f"Error syncing from server: {str(e)}")
            return False
    
    def _toggle_ui_lock(self, lock):
        """Lock or unlock the UI during synchronization"""
        if not self.parent or not hasattr(self.parent, 'notebook'):
            return
            
        state = "disabled" if lock else "normal"
        
        # Disable all tabs except the current one
        for i in range(self.parent.notebook.index("end")):
            if i != self.parent.notebook.index("current"):
                self.parent.notebook.tab(i, state=state)
        
        # Update a status message if available
        if hasattr(self.parent, 'status_var'):
            self.parent.status_var.set("Synchronizing with server..." if lock else "")
            
        # Process events to update UI
        self.parent.root.update()
    
    def _show_error(self, title, message):
        """Show an error message dialog"""
        if self.parent and hasattr(self.parent, 'root'):
            messagebox.showerror(title, message, parent=self.parent.root)
        else:
            logger.log_error(f"{title}: {message}")
    
    def _show_success(self, title, message):
        """Show a success message dialog"""
        if self.parent and hasattr(self.parent, 'root'):
            messagebox.showinfo(title, message, parent=self.parent.root)
        else:
            logger.log_debug(f"{title}: {message}")
