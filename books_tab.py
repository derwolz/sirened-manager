import tkinter as tk
from tkinter import ttk, messagebox
import re
from csv_import_handler import CSVImportHandler
import json
import app_logger as logger
from book_image_preview import BookImagePreview
class BooksTab:
    def __init__(self, parent):
        self.parent = parent
        
        # Create tab
        self.frame = ttk.Frame(parent.notebook)
        parent.notebook.add(self.frame, text="Books")
        
        self.setup_tab()
        self.csv_import_handler = CSVImportHandler(self)
    
    def setup_tab(self):
        # Split frame into two main sections
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Books list frame (left side)
        books_list_frame = ttk.Frame(main_frame)
        books_list_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10)
        
        # Books list
        ttk.Label(books_list_frame, text="Books:").pack(anchor=tk.W)
        self.books_listbox = tk.Listbox(books_list_frame, width=30, height=20)
        self.books_listbox.pack(fill=tk.BOTH, expand=True)
        self.books_listbox.bind('<<ListboxSelect>>', self.on_book_select)
        
        # Buttons for book management
        btn_frame = ttk.Frame(books_list_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Add New", command=self.add_book).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete", command=self.delete_book).pack(side=tk.LEFT, padx=5)
        
        # Create a right panel that contains book details and image preview
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Book details frame (in the right panel)
        self.book_details_frame = ttk.Frame(right_panel)
        self.book_details_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Initialize the image preview component (in the right panel)
        self.image_preview = BookImagePreview(right_panel)
        
        # Create a canvas with scrollbar for book fields
        canvas = tk.Canvas(self.book_details_frame)
        scrollbar = ttk.Scrollbar(self.book_details_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Book fields
        # Title
        ttk.Label(scrollable_frame, text="Title*:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.book_title_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.book_title_var, width=40).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Author selection
        ttk.Label(scrollable_frame, text="Author*:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.book_author_var = tk.StringVar()
        self.book_author_combo = ttk.Combobox(scrollable_frame, textvariable=self.book_author_var, width=38)
        self.book_author_combo.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Description
        ttk.Label(scrollable_frame, text="Description*:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.book_description_text = tk.Text(scrollable_frame, width=40, height=4)
        self.book_description_text.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Internal details
        ttk.Label(scrollable_frame, text="Internal Details:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.internal_details_text = tk.Text(scrollable_frame, width=40, height=3)
        self.internal_details_text.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Page count
        ttk.Label(scrollable_frame, text="Page Count*:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.page_count_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.page_count_var, width=40).grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # Formats
        ttk.Label(scrollable_frame, text="Formats*:").grid(row=5, column=0, sticky=tk.W, pady=5)
        formats_frame = ttk.Frame(scrollable_frame)
        formats_frame.grid(row=5, column=1, sticky=tk.W, pady=5)
        
        self.format_digital = tk.BooleanVar()
        self.format_softback = tk.BooleanVar()
        self.format_hardback = tk.BooleanVar()
        self.format_audiobook = tk.BooleanVar()
        
        ttk.Checkbutton(formats_frame, text="Digital", variable=self.format_digital).pack(side=tk.LEFT)
        ttk.Checkbutton(formats_frame, text="Softback", variable=self.format_softback).pack(side=tk.LEFT)
        ttk.Checkbutton(formats_frame, text="Hardback", variable=self.format_hardback).pack(side=tk.LEFT)
        ttk.Checkbutton(formats_frame, text="Audiobook", variable=self.format_audiobook).pack(side=tk.LEFT)
        
        # Publish date
        ttk.Label(scrollable_frame, text="Publish Date (YYYY-MM-DD)*:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.publish_date_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.publish_date_var, width=40).grid(row=6, column=1, sticky=tk.W, pady=5)
        
        # Awards
        ttk.Label(scrollable_frame, text="Awards:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.awards_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.awards_var, width=40).grid(row=7, column=1, sticky=tk.W, pady=5)
        
        # Series
        ttk.Label(scrollable_frame, text="Series:").grid(row=8, column=0, sticky=tk.W, pady=5)
        self.series_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.series_var, width=40).grid(row=8, column=1, sticky=tk.W, pady=5)
        
        # Setting
        ttk.Label(scrollable_frame, text="Setting:").grid(row=9, column=0, sticky=tk.W, pady=5)
        self.setting_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.setting_var, width=40).grid(row=9, column=1, sticky=tk.W, pady=5)
        
        # Characters
        ttk.Label(scrollable_frame, text="Characters (comma separated):").grid(row=10, column=0, sticky=tk.W, pady=5)
        self.characters_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.characters_var, width=40).grid(row=10, column=1, sticky=tk.W, pady=5)
        
        # Language
        ttk.Label(scrollable_frame, text="Language*:").grid(row=11, column=0, sticky=tk.W, pady=5)
        self.language_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.language_var, width=40).grid(row=11, column=1, sticky=tk.W, pady=5)
        
        # Referral links
        ttk.Label(scrollable_frame, text="Referral Links:").grid(row=12, column=0, sticky=tk.W, pady=5)
        self.referral_links_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.referral_links_var, width=40).grid(row=12, column=1, sticky=tk.W, pady=5)
        
        # Save button
        ttk.Button(scrollable_frame, text="Save Book", command=self.save_book).grid(
            row=13, column=0, columnspan=2, pady=10
        )
    def log_debug(self, message):
        """Simple method to log debug info"""
        if hasattr(logger, 'log_debug'):
            logger.log_debug(message)
        else:
            print(f"DEBUG: {message}")

    def update_book_author_dropdown(self):
        """Update author selection dropdown in books tab"""
        author_names = []
        
        # Log debug info
        logger.log_debug(f"Updating book author dropdown. Publisher mode: {self.parent.is_publisher.get()}")
        
        try:
            # Use the new method from DatabaseManager
            authors_raw = self.parent.db_manager.authors.get_all()
            logger.log_debug(f"Got {len(authors_raw)} authors from DB")
            
            for author in authors_raw:
                # author is a tuple from the database query
                # index 2 is typically the author_name
                if len(author) > 2 and author[2]:
                    author_name = author[2]
                    author_names.append(author_name)
                    logger.log_debug(f"Added author: {author_name}")
        
        except Exception as e:
            logger.log_error(f"Error getting authors: {str(e)}")
        
        # Set the values in the combobox
        self.book_author_combo['values'] = author_names
        
        # If we're in publisher mode and there are no authors, show a warning
        if self.parent.is_publisher.get() and not author_names:
            logger.log_error("No authors found for publisher mode")
    def add_book(self):
            """Add a new book to the list"""
            self.clear_book_fields()
            self.update_books_listbox()

    
            return len(author_names) > 0
    def force_author_dropdown_update(self):
        """Force reload authors from database and update dropdown"""
        author_names = []
        
        try:
            logger.log_debug("Force loading authors from database")
            authors_db = self.parent.db_manager.authors.get_all()
            logger.log_debug(f"Forced load got {len(authors_db)} authors from DB")
            
            # Dump one author record to see structure
            if authors_db:
                logger.log_debug(f"Sample author structure: {authors_db[0]}")
            
            for author in authors_db:
                if len(author) > 2 and author[2]:  # index 2 should be author_name
                    author_name = author[2]
                    author_names.append(author_name)
                    logger.log_debug(f"Added forced DB author: {author_name}")
        except Exception as e:
            logger.log_error(f"Error in force loading authors: {str(e)}")
        
        # Update dropdown
        self.book_author_combo['values'] = author_names
        logger.log_debug(f"Force updated author dropdown with {len(author_names)} names")

    def save_book(self):

        """Save current book data"""
        title = self.book_title_var.get().strip()
        author = self.book_author_var.get().strip()
        description = self.book_description_text.get("1.0", tk.END).strip()
        page_count = self.page_count_var.get().strip()
        publish_date = self.publish_date_var.get().strip()
        language = self.language_var.get().strip()
        
        # Validate required fields
        if not title:
            messagebox.showerror("Error", "Title is required")
            return
        
        if not author:
            messagebox.showerror("Error", "Author is required")
            return
        
        if not description:
            messagebox.showerror("Error", "Description is required")
            return
        
        if not page_count:
            messagebox.showerror("Error", "Page count is required")
            return
        
        if not publish_date:
            messagebox.showerror("Error", "Publish date is required")
            return
        
        if not language:
            messagebox.showerror("Error", "Language is required")
            return
        
        # Validate page count
        try:
            page_count = int(page_count)
            if page_count <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Page count must be a positive number")
            return
        
        # Validate publish date
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", publish_date):
            messagebox.showerror("Error", "Publish date must be in YYYY-MM-DD format")
            return
        
        # Check if at least one format is selected
        formats = []
        if self.format_digital.get():
            formats.append("digital")
        if self.format_softback.get():
            formats.append("softback")
        if self.format_hardback.get():
            formats.append("hardback")
        if self.format_audiobook.get():
            formats.append("audiobook")
        
        if not formats:
            messagebox.showerror("Error", "At least one format must be selected")
            return
        
        # If in publisher mode, verify that author exists and get author_id
        author_id = None
        if author:
                # Try to find author ID from the database
                author_results = self.parent.db_manager.execute_query(
                    "SELECT id FROM authors WHERE author_name = ?", 
                    (author,)
                )
                if author_results:
                    author_id = author_results[0][0]
                    logger.log_debug(f"Found author ID {author_id} for author {author}")
        
        # Get all book data
        book_data = {
            "title": title,
            "author": author,
            "author_id": author_id,  # Store author ID for database relation
            "description": description,
            "internal_details": self.internal_details_text.get("1.0", tk.END).strip(),
            "page_count": page_count,
            "formats": formats,
            "publish_date": publish_date,
            "awards": self.awards_var.get().strip(),
            "series": self.series_var.get().strip(),
            "setting": self.setting_var.get().strip(),
            "characters": [c.strip() for c in self.characters_var.get().split(",") if c.strip()],
            "language": language,
            "referral_links": self.referral_links_var.get().strip()
        }
        self.log_debug(book_data)
        # Check if book already exists
        book_index = None
        for i, book in enumerate(self.parent.books):
            if book["title"] == title:
                book_index = i
                break
        
        if book_index is not None:
            # Update existing book
            self.parent.books[book_index] = book_data
        else:
            # Add new book
            self.parent.books.append(book_data)
        
        # Update UI
        self.update_books_listbox()
        self.parent.genres_tab.update_genre_book_dropdown()
        self.parent.images_tab.update_image_item_dropdown()
        self.parent.update_export_status()
        
        messagebox.showinfo("Success", f"Book '{title}' saved successfully")
    
    def delete_book(self):
        """Delete the selected book"""
        selected_indices = self.books_listbox.curselection()
        
        if not selected_indices:
            messagebox.showerror("Error", "No book selected")
            return
        
        index = selected_indices[0]
        if index < len(self.parent.books):
            book_title = self.parent.books[index]["title"]
            
            # Check if book has genre relations
            for relation in self.parent.genre_relations:
                if relation["book"] == book_title:
                    messagebox.showerror(
                        "Error", 
                        f"Cannot delete book '{book_title}' because it has associated genre relations"
                    )
                    return
            
            # Check if book has images
            for image in self.parent.images:
                if image["item_type"] == "Book" and image["item"] == book_title:
                    messagebox.showerror(
                        "Error", 
                        f"Cannot delete book '{book_title}' because it has associated images"
                    )
                    return
            
            # Delete book
            del self.parent.books[index]
            self.update_books_listbox()
            self.clear_book_fields()
            self.parent.genres_tab.update_genre_book_dropdown()
            self.parent.images_tab.update_image_item_dropdown()
            self.parent.update_export_status()
            messagebox.showinfo("Success", f"Book '{book_title}' deleted successfully")
    
    def on_book_select(self, event):
        """Handle book selection"""
        selected_indices = self.books_listbox.curselection()
        
        if not selected_indices:
            return
        
        index = selected_indices[0]
        if index < len(self.parent.books):
            book = self.parent.books[index]
            logger.log_debug(f"Selected book data: {book}")
            
            # Clear all fields first
            self.clear_book_fields()
            
            # Get book ID for image lookup
            book_id = None
            
            # Fill in book data - correctly handling dict or tuple type
            if isinstance(book, dict):
                # Handle dictionary format
                self.book_title_var.set(book.get("title", ""))
                self.book_author_var.set(book.get("author", ""))
                
                if book.get("description"):
                    self.book_description_text.insert("1.0", book.get("description", ""))
                    
                if book.get("internal_details"):
                    self.internal_details_text.insert("1.0", book.get("internal_details", ""))
                    
                self.page_count_var.set(str(book.get("page_count", 0)))
                
                # Set formats
                formats = book.get("formats", [])
                if isinstance(formats, str):
                    try:
                        formats = json.loads(formats)
                    except:
                        formats = formats.split(",") if "," in formats else [formats]
                
                self.format_digital.set("digital" in formats)
                self.format_softback.set("softback" in formats)
                self.format_hardback.set("hardback" in formats)
                self.format_audiobook.set("audiobook" in formats)
                
                # Set other fields
                self.publish_date_var.set(book.get("publish_date", ""))
                self.awards_var.set(book.get("awards", ""))
                self.series_var.set(book.get("series", ""))
                self.setting_var.set(book.get("setting", ""))
                
                # Characters
                characters = book.get("characters", [])
                if isinstance(characters, str):
                    try:
                        characters = json.loads(characters)
                    except:
                        characters = characters.split(",") if "," in characters else [characters]
                        
                self.characters_var.set(", ".join(characters) if characters else "")
                self.language_var.set(book.get("language", "English"))
                self.referral_links_var.set(book.get("referral_links", ""))
                
                # Get book ID for image lookup
                book_id = book.get("id")
                
            else:
                # Handle tuple format (database row)
                book_id = book[0] if len(book) > 0 else None  # book ID should be the first element
                
                self.book_title_var.set(book[1] if len(book) > 1 else "")  # title
                
                # Try to get author - it could be in multiple places depending on the query
                author_name = None
                
                # First check the 'author' field (index 2)
                if len(book) > 2 and book[2]:
                    author_name = book[2]
                    logger.log_debug(f"Using author name from index 2: {author_name}")
                
                # If no author found, try the effective_author field that might be returned
                # by JOIN queries (usually at the end of the tuple)
                elif len(book) > 25 and book[25]:  # Check for effective_author at index 25
                    author_name = book[25]
                    logger.log_debug(f"Using effective_author from index 25: {author_name}")
                
                # If we found an author, set it
                if author_name:
                    self.book_author_var.set(author_name)
                    
                    # Make sure this author is in the dropdown
                    current_values = list(self.book_author_combo['values'])
                    if author_name not in current_values:
                        current_values.append(author_name)
                        self.book_author_combo['values'] = current_values
                else:
                    logger.log_debug("No author found for this book")
                
                # Fill in the rest of the fields
                if len(book) > 4 and book[4]:  # description
                    self.book_description_text.insert("1.0", book[4])
                
                # Handle internal details (index 23)
                if len(book) > 23 and book[23]:
                    self.internal_details_text.insert("1.0", book[23])
                
                # Set page count (index 7)
                if len(book) > 7:
                    self.page_count_var.set(str(book[7] or 0))
                
                # Handle formats (index 8)
                formats = []
                if len(book) > 8 and book[8]:
                    try:
                        formats = json.loads(book[8])
                    except:
                        formats = book[8].split(",") if isinstance(book[8], str) and "," in book[8] else [book[8]]
                
                self.format_digital.set("digital" in formats)
                self.format_softback.set("softback" in formats)
                self.format_hardback.set("hardback" in formats)
                self.format_audiobook.set("audiobook" in formats)
                
                # Set other fields
                if len(book) > 9:
                    self.publish_date_var.set(book[9] or "")  # publishedDate
                if len(book) > 10:
                    self.awards_var.set(book[10] or "")  # awards
                if len(book) > 12:
                    self.series_var.set(book[12] or "")  # series
                if len(book) > 13:
                    self.setting_var.set(book[13] or "")  # setting
                
                # Handle characters (index 14)
                characters = []
                if len(book) > 14 and book[14]:
                    try:
                        characters = json.loads(book[14])
                    except:
                        characters = book[14].split(",") if isinstance(book[14], str) and "," in book[14] else [book[14]]
                
                self.characters_var.set(", ".join(characters) if characters else "")
                
                # Language (index 17)
                if len(book) > 17:
                    self.language_var.set(book[17] or "English")
                
                # Referral links (index 18)
                if len(book) > 18:
                    self.referral_links_var.set(book[18] or "")
            
            # Update image preview if book_id is available
            if book_id and hasattr(self, 'image_preview'):
                logger.log_debug(f"Updating image preview for book ID: {book_id}")
                self.image_preview.update_previews(self.parent.db_manager, book_id)    
    def clear_book_fields(self):
        """Clear all book fields"""
        self.book_title_var.set("")
        self.book_author_var.set("")
        self.book_description_text.delete("1.0", tk.END)
        self.internal_details_text.delete("1.0", tk.END)
        self.page_count_var.set("")
        self.format_digital.set(False)
        self.format_softback.set(False)
        self.format_hardback.set(False)
        self.format_audiobook.set(False)
        self.publish_date_var.set("")
        self.awards_var.set("")
        self.series_var.set("")
        self.setting_var.set("")
        self.characters_var.set("")
        self.language_var.set("")
        self.referral_links_var.set("")
    
    def update_books_listbox(self):
        """Update the books listbox"""
        self.books_listbox.delete(0, tk.END)
        # Get latest books from database with author information
        self.parent.books = self.parent.db_manager.books.get_all()
        for book in self.parent.books:
            self.books_listbox.insert(tk.END, book[1])
            
    def load_books_from_database(self, db_manager):
        logger.log_debug("loading from db")
        """Load books from the database with proper author information"""
        # Clear existing books
        self.parent.books = []
        
        # Get books with author information from database
        self.parent.books = db_manager.books.get_all()

        self.update_books_listbox()
        self.update_book_author_dropdown()

    

        

