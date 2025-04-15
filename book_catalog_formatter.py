import tkinter as tk
from tkinter import ttk
import os
import requests
import app_logger as logger  # Import the standalone logger module
from config import (
    API_BASE_URL, 
    LOGIN_ENDPOINT, 
    AUTHOR_STATUS_ENDPOINT, 
    PUBLISHER_STATUS_ENDPOINT
)
from settings_tab import SettingsTab
from authors_tab import AuthorsTab
from books_tab import BooksTab
from genres_tab import GenresTab
from authentication_tab import AuthenticationTab

class BookCatalogFormatter:
    def __init__(self, root, db_manager):
        self.root = root
        self.root.title("Book Catalog Formatter")
        self.root.geometry("1200x800")
        
        # Store database manager
        self.db_manager = db_manager
        
        # API base URL
        self.api_base_url = API_BASE_URL
        
        # Data storage (will be populated from database)
        self.authors = []
        self.books = []
        self.genre_relations = []
        
        # Authentication data
        self.cookies = None
        self.is_authenticated = tk.BooleanVar(value=False)
        self.is_author = tk.BooleanVar(value=False)
        self.is_publisher = tk.BooleanVar(value=False)
        
        # Create the main notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Setup tabs in correct order
        self.authentication_tab = self.create_authentication_tab()
        self.settings_tab = self.create_settings_tab()
        self.authors_tab = self.create_authors_tab()
        self.books_tab = self.create_books_tab()
        self.genres_tab = self.create_genres_tab()
        
        # Store tab indexes for easier reference
        self.tab_indexes = {
            "authentication": 0,
            "settings": 1,
            "authors": 2,
            "books": 3,
            "genres": 4,
        }
        
        # Create debugging and error message frames
        self.create_debug_frames()
        
        # Bind events
        self.is_publisher.trace_add("write", self.update_tab_permissions)
        self.is_author.trace_add("write", self.update_tab_permissions)
        self.is_authenticated.trace_add("write", self.update_tab_permissions)
        
        # Load data from database
        self.load_data_from_database()
        
        # Disable all tabs except authentication initially
        self.disable_all_tabs_except_auth()
        
        logger.log_debug("BookCatalogFormatter initialized")
        
    def create_authentication_tab(self):
        """Factory method to create authentication tab"""
        return AuthenticationTab(self)
    
    def create_settings_tab(self):
        """Factory method to create settings tab"""
        return SettingsTab(self)
    
    def create_authors_tab(self):
        """Factory method to create authors tab"""
        return AuthorsTab(self)
    
    def create_books_tab(self):
        """Factory method to create books tab"""
        return BooksTab(self)
    
    def create_genres_tab(self):
        """Factory method to create genres tab"""
        return GenresTab(self)
    
    
    
    def load_data_from_database(self):
        """Load initial data from database"""
        try:
            # Load authors
            self.authors = self.db_manager.authors.get_all()
            
            # Load books
            self.books = self.db_manager.books.get_all()
            
            # Load genres (will be loaded as needed in the genres tab)
            
            # Load saved settings
            self.load_settings()
            
        except Exception as e:
            logger.log_error(f"Error loading data from database: {str(e)}")
    
    def load_settings(self):
        """Load user settings from database"""
        try:
            # Check if we have a saved publisher setting
            is_publisher = self.db_manager.settings.get("is_publisher", "0")
            self.is_publisher.set(is_publisher == "1")
            
            # Load any other settings as needed
        except Exception as e:
            logger.log_error(f"Error loading settings: {str(e)}")
    
    def save_settings(self):
        """Save user settings to database"""
        try:
            # Save publisher setting
            self.db_manager.settings.set("is_publisher", "1" if self.is_publisher.get() else "0")
            
            # Save any other settings as needed
        except Exception as e:
            logger.log_error(f"Error saving settings: {str(e)}")
    
    def get_api_url(self, endpoint):
        """Construct full API URL from base URL and endpoint"""
        return f"{self.api_base_url}{endpoint}"
    
    def api_request(self, method, endpoint, data=None, headers=None):
        """Make an API request with proper error handling"""
        url = self.get_api_url(endpoint)
        
        if headers is None:
            headers = {}
        
        try:
            logger.log_debug(f"Making {method} request to {url}")
            
            if method.upper() == "GET":
                response = requests.get(url, cookies=self.cookies, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, cookies=self.cookies, headers=headers)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, cookies=self.cookies, headers=headers)
            elif method.upper() == "DELETE":
                response = requests.delete(url, cookies=self.cookies, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            if response.status_code >= 400:
                logger.log_error(f"API Error ({response.status_code}): {response.text}")
                
            return response
        except Exception as e:
            logger.log_error(f"API Request error: {str(e)}")
            raise
    
    def check_author_status(self):
        """Check if the current user is an author"""
        try:
            logger.log_debug("Checking author status...")
            response = self.api_request("GET", AUTHOR_STATUS_ENDPOINT)
            
            if response.status_code == 200:
                data = response.json()
                is_author = data.get("isAuthor", False)
                self.is_author.set(is_author)
                
                logger.log_debug(f"Author status: {is_author}")
                
                # Store author details if available
                if is_author and "authorDetails" in data:
                    self.author_details = data["authorDetails"]
                
                return is_author
            return False
        except Exception as e:
            logger.log_error(f"Error checking author status: {str(e)}")
            return False
    
    def check_publisher_status(self):
        """Check if the current user is a publisher"""
        try:
            logger.log_debug("Checking publisher status...")
            response = self.api_request("GET", PUBLISHER_STATUS_ENDPOINT)
            
            if response.status_code == 200:
                data = response.json()
                is_publisher = data.get("isPublisher", False)
                self.is_publisher.set(is_publisher)
                
                logger.log_debug(f"Publisher status: {is_publisher}")
                
                # Store publisher details if available
                if is_publisher and "publisherDetails" in data:
                    self.publisher_details = data["publisherDetails"]
                
                self.save_settings()  # Save settings after updating publisher status
                return is_publisher
            return False
        except Exception as e:
            logger.log_error(f"Error checking publisher status: {str(e)}")
            return False
    
    def disable_all_tabs_except_auth(self):
        """Initial setup to disable all tabs except authentication"""
        for i in range(1, 5):  # All tabs except authentication (index 0)
            self.notebook.tab(i, state="disabled")
    
    def update_tab_permissions(self, *args):
        """Update tab states based on user role (publisher, author, or regular user)"""
        # Only proceed if authenticated
        if not self.is_authenticated.get():
            # If not authenticated, disable all tabs except authentication
            self.disable_all_tabs_except_auth()
            self.notebook.select(self.tab_indexes["authentication"])
            return
        
        # Get current role states
        is_publisher = self.is_publisher.get()
        is_author = self.is_author.get()
        
        logger.log_debug(f"Updating permissions: Publisher={is_publisher}, Author={is_author}")
        
        # PUBLISHER: Access to everything
        if is_publisher:
            for tab_name, tab_index in self.tab_indexes.items():
                if tab_name != "authentication":
                    self.notebook.tab(tab_index, state="normal")
                    
                
        # AUTHOR: Access to Books, Events , Settings, and Genres
        elif is_author:
            # Enable author-accessible tabs
            for tab_name in ["settings", "books", "genres" ]:
                self.notebook.tab(self.tab_indexes[tab_name], state="normal")
                
            # Disable Authors tab
            self.notebook.tab(self.tab_indexes["authors"], state="disabled")
            
                
        # REGULAR USER: Limited access
        else:
            # Disable Authors tab
            self.notebook.tab(self.tab_indexes["authors"], state="disabled")
            
            # Enable basic tabs
            for tab_name in ["settings", "books", "genres"]:
                self.notebook.tab(self.tab_indexes[tab_name], state="normal")
                
        
        # Update related dropdowns if they exist
        self.refresh_ui_elements()
            
        # If just logged in, select the Settings tab to begin workflow
        if self.notebook.index("current") == self.tab_indexes["authentication"]:
            self.notebook.select(self.tab_indexes["settings"])
    
    def refresh_ui_elements(self):
        """Refresh UI elements after role changes"""
        # Update book author dropdown
        if hasattr(self.books_tab, 'update_book_author_dropdown'):
            self.books_tab.update_book_author_dropdown()
            
        # Update genre book dropdown
        if hasattr(self.genres_tab, 'update_genre_book_dropdown'):
            self.genres_tab.update_genre_book_dropdown()
            
    
            
    # ===== DEBUGGING AND ERROR HANDLING =====
    
    def create_debug_frames(self):
        """Create debug and error message frames at the bottom of the application"""
        # Create a frame for the debug section at the bottom
        self.debug_frame = ttk.Frame(self.root)
        self.debug_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0, 5))
        
        # Create notebook for debug and error tabs
        self.debug_notebook = ttk.Notebook(self.debug_frame)
        self.debug_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create debug log tab
        self.debug_tab = ttk.Frame(self.debug_notebook)
        self.debug_notebook.add(self.debug_tab, text="Debug Log")
        
        # Create debug text widget with scroll
        self.debug_scroll = ttk.Scrollbar(self.debug_tab)
        self.debug_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.debug_text = tk.Text(self.debug_tab, height=10, yscrollcommand=self.debug_scroll.set, wrap=tk.WORD)
        self.debug_text.pack(fill=tk.BOTH, expand=True)
        self.debug_scroll.config(command=self.debug_text.yview)
        
        # Create debug controls
        self.debug_controls = ttk.Frame(self.debug_tab)
        self.debug_controls.pack(fill=tk.X, pady=5)
        
        self.clear_debug_btn = ttk.Button(self.debug_controls, text="Clear Debug Log", 
                                          command=logger.clear_debug_log)
        self.clear_debug_btn.pack(side=tk.LEFT, padx=5)
        
        self.debug_enabled = tk.BooleanVar(value=True)
        self.debug_toggle = ttk.Checkbutton(self.debug_controls, text="Enable Debug Logging", 
                                           variable=self.debug_enabled, 
                                           command=lambda: logger.set_debug_enabled(self.debug_enabled.get()))
        self.debug_toggle.pack(side=tk.LEFT, padx=5)
        
        # Create error log tab
        self.error_tab = ttk.Frame(self.debug_notebook)
        self.debug_notebook.add(self.error_tab, text="Error Log")
        
        # Create error text widget with scroll
        self.error_scroll = ttk.Scrollbar(self.error_tab)
        self.error_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.error_text = tk.Text(self.error_tab, height=10, yscrollcommand=self.error_scroll.set, 
                                 wrap=tk.WORD, background="#fff0f0")
        self.error_text.pack(fill=tk.BOTH, expand=True)
        self.error_scroll.config(command=self.error_text.yview)
        
        # Create error controls
        self.error_controls = ttk.Frame(self.error_tab)
        self.error_controls.pack(fill=tk.X, pady=5)
        
        self.clear_error_btn = ttk.Button(self.error_controls, text="Clear Error Log", 
                                          command=logger.clear_error_log)
        self.clear_error_btn.pack(side=tk.LEFT, padx=5)
        
        # Collapse button to minimize the debug section
        self.debug_visible = tk.BooleanVar(value=True)
        self.toggle_debug_btn = ttk.Button(self.debug_frame, text="▲ Hide Debug", command=self.toggle_debug_visibility)
        self.toggle_debug_btn.pack(fill=tk.X, pady=(5, 0))
        
        # Initialize the logger module with our UI components
        logger.initialize(self.root, self.debug_text, self.error_text, self.debug_notebook)
        
    def toggle_debug_visibility(self):
        """Toggle the visibility of the debug section"""
        if self.debug_visible.get():
            self.debug_notebook.pack_forget()
            self.debug_visible.set(False)
            self.toggle_debug_btn.configure(text="▼ Show Debug")
        else:
            self.debug_notebook.pack(fill=tk.BOTH, expand=True)
            self.debug_visible.set(True)
            self.toggle_debug_btn.configure(text="▲ Hide Debug")
