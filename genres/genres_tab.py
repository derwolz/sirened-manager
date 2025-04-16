import tkinter as tk
from tkinter import ttk, messagebox
import json
from csv_import_handler import CSVImportHandler
from tkinter import simpledialog

# Import component modules
from .book_selector import BookSelector
from .taxonomy_selector import TaxonomySelector
from .selected_taxonomies import SelectedTaxonomies

class GenresTab:
    def __init__(self, parent):
        """
        Initialize the genres tab
        
        Args:
            parent: The parent application
        """
        self.parent = parent
        
        # Create tab
        self.frame = ttk.Frame(parent.notebook)
        parent.notebook.add(self.frame, text="Genres")
        
        # Initialize data structures
        if not hasattr(self.parent, 'book_taxonomies'):
            self.parent.book_taxonomies = []  # Will store book-taxonomy relationships
            
        self.current_book_id = None
        self.current_taxonomies = []
        
        # Set up UI components
        self.setup_tab()
        
        # Initialize CSV import handler
        self.csv_import_handler = CSVImportHandler(self)
    
    def setup_tab(self):
        """Set up the main tab UI"""
        # Main split pane
        main_pane = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side - Book selection and taxonomy types
        left_frame = ttk.Frame(main_pane)
        main_pane.add(left_frame, weight=1)
        
        # Initialize components
        self.book_selector = BookSelector(left_frame, self)
        self.book_selector.get_frame().pack(fill=tk.X, padx=5, pady=5)
        
        self.taxonomy_selector = TaxonomySelector(left_frame, self)
        self.taxonomy_selector.get_frame().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right side - Selected taxonomies
        right_frame = ttk.Frame(main_pane)
        main_pane.add(right_frame, weight=1)
        
        self.selected_taxonomies = SelectedTaxonomies(right_frame, self)
        self.selected_taxonomies.get_frame().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Import button for genres
        import_frame = ttk.Frame(self.frame)
        import_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(import_frame, text="Import Genres from JSON", command=self.import_genres_json).pack(side=tk.LEFT, padx=5)
    
    def update_genre_book_dropdown(self):
        """Update book selection dropdown in genres tab"""
        books_data = []
        
        # Get books data from database instead of relying on parent.books
        if hasattr(self.parent, 'db_manager'):
            try:
                # Use the books model to get all books with author information
                books_data = self.parent.db_manager.books.get_all()
                
                # Convert tuple results to dictionaries
                formatted_books = []
                for book in books_data:
                    # Extract relevant fields - adjust indices based on your schema
                    book_dict = {
                        "id": book[0],  # id
                        "title": book[1],  # title
                        "author": book[2] if book[2] else book[21],  # author or effective_author
                        "authorId": book[3]  # authorId
                    }
                    formatted_books.append(book_dict)
                
                books_data = formatted_books
            except Exception as e:
                import app_logger as logger
                logger.log_error(f"Error fetching books from database: {str(e)}")
                # Fallback to parent.books if database query fails
                for book in self.parent.books:
                    if isinstance(book, dict):
                        books_data.append(book)
        else:
            # Fallback if no database manager
            for book in self.parent.books:
                if isinstance(book, dict):
                    books_data.append(book)
        
        # Update book selector with books data
        self.book_selector.update_books(books_data)
    
    # Communication methods for components
    
    def on_book_selected(self, book_id):
        """
        Handle book selection (called by BookSelector)
        
        Args:
            book_id: ID of the selected book
        """
        self.current_book_id = book_id
        
        # Load taxonomies for this book
        self.load_book_taxonomies(book_id)
        
        # Update UI - order matters here!
        # First update the selected taxonomies display
        self.selected_taxonomies.update_selected_listbox(self.current_taxonomies)
        
        # Then update the counts in the tab headers
        self.update_taxonomy_counts()
        
        # Finally refresh the taxonomy selector lists to exclude already selected items
        self.taxonomy_selector.refresh_all_taxonomies()
    
    def get_taxonomies_by_type(self, taxonomy_type):
        """
        Get all taxonomies of a specific type (called by TaxonomySelector)
        
        Args:
            taxonomy_type: Type of taxonomy to get
            
        Returns:
            List of taxonomy dictionaries
        """
        # First try to get taxonomies from database
        if hasattr(self.parent, 'db_manager'):
            try:
                query = """
                SELECT id, name, description, type, parentId
                FROM genres
                WHERE type = ? OR (? = 'genre' AND (type IS NULL OR type = ''))
                ORDER BY name
                """
                
                results = self.parent.db_manager.execute_query(query, (taxonomy_type, taxonomy_type))
                
                taxonomies = []
                for result in results:
                    taxonomy_id, name, description, db_type, parent_id = result
                    taxonomies.append({
                        "id": taxonomy_id,
                        "name": name,
                        "description": description,
                        "type": taxonomy_type,  # Use the requested type if db_type is None
                        "parentId": parent_id
                    })
                
                return taxonomies
            except Exception as e:
                import app_logger as logger
                logger.log_error(f"Error fetching taxonomies from database: {str(e)}")
        
        # Fallback to parent.genres
        if not hasattr(self.parent, 'genres'):
            return []
            
        taxonomies = []
        for genre in self.parent.genres:
            if isinstance(genre, dict) and genre.get("type", "genre") == taxonomy_type:
                taxonomies.append(genre)
        
        return taxonomies
    
    def get_current_taxonomies(self):
        """
        Get current taxonomies (called by TaxonomySelector and SelectedTaxonomies)
        
        Returns:
            List of current taxonomy dictionaries
        """
        return self.current_taxonomies
    
    def add_taxonomy(self, taxonomy_type, taxonomy_id):
        """
        Add a taxonomy to selected list (called by TaxonomySelector)
        
        Args:
            taxonomy_type: Type of taxonomy to add
            taxonomy_id: ID of the taxonomy to add
            
        Returns:
            Boolean indicating success
        """
        if not self.current_book_id:
            messagebox.showinfo("Information", "Please select a book first")
            return False
        
        # Get the taxonomy info
        taxonomy_info = None
        for taxonomy in self.get_taxonomies_by_type(taxonomy_type):
            if taxonomy.get("id") == taxonomy_id:
                taxonomy_info = taxonomy
                break
        
        if not taxonomy_info:
            messagebox.showerror("Error", f"{taxonomy_type.capitalize()} not found in database")
            return False
        
        # Check if already selected
        for existing in self.current_taxonomies:
            if existing.get("taxonomyId") == taxonomy_id:
                messagebox.showinfo("Information", 
                                 f"This {taxonomy_type} is already selected")
                return False
        
        # Check if we've reached the maximum for this type
        type_count = sum(1 for t in self.current_taxonomies if t.get("type") == taxonomy_type)
        max_counts = {"genre": 2, "subgenre": 5, "theme": 6, "trope": 7}
        
        if type_count >= max_counts.get(taxonomy_type, 0):
            messagebox.showinfo("Information", 
                             f"Maximum of {max_counts.get(taxonomy_type)} {taxonomy_type}s already selected")
            return False
        
        # Add the taxonomy
        next_rank = len(self.current_taxonomies) + 1
        new_taxonomy = {
            "taxonomyId": taxonomy_id,
            "type": taxonomy_type,
            "rank": next_rank,
            "name": taxonomy_info.get("name", "")
        }
        
        self.current_taxonomies.append(new_taxonomy)
        
        # Update UI
        self.selected_taxonomies.update_selected_listbox(self.current_taxonomies)
        self.update_taxonomy_counts()
        
        # Refresh taxonomy selectors to filter out the newly added taxonomy
        self.taxonomy_selector.refresh_all_taxonomies()
        
        return True
    
    def move_taxonomy(self, index, direction):
        """
        Move a taxonomy up or down (called by SelectedTaxonomies)
        
        Args:
            index: Index of the taxonomy to move
            direction: Direction to move ("up" or "down")
        """
        if index < 0 or index >= len(self.current_taxonomies):
            return
        
        if direction == "up" and index > 0:
            # Swap with previous
            self.current_taxonomies[index], self.current_taxonomies[index-1] = \
                self.current_taxonomies[index-1], self.current_taxonomies[index]
        elif direction == "down" and index < len(self.current_taxonomies) - 1:
            # Swap with next
            self.current_taxonomies[index], self.current_taxonomies[index+1] = \
                self.current_taxonomies[index+1], self.current_taxonomies[index]
        else:
            return
        
        # Update ranks
        for i, taxonomy in enumerate(self.current_taxonomies):
            taxonomy["rank"] = i + 1
        
        # Update UI
        self.selected_taxonomies.update_selected_listbox(self.current_taxonomies)
    
    def remove_taxonomy(self, index):
        """
        Remove a taxonomy (called by SelectedTaxonomies)
        
        Args:
            index: Index of the taxonomy to remove
        """
        if index < 0 or index >= len(self.current_taxonomies):
            return
        
        # Remove taxonomy
        self.current_taxonomies.pop(index)
        
        # Reorder ranks
        for i, taxonomy in enumerate(self.current_taxonomies):
            taxonomy["rank"] = i + 1
        
        # Update UI
        self.selected_taxonomies.update_selected_listbox(self.current_taxonomies)
        self.update_taxonomy_counts()
        
        # Refresh taxonomy selectors to include the removed taxonomy
        self.taxonomy_selector.refresh_all_taxonomies()
    
    def save_taxonomies(self):
        """Save the current taxonomies (called by SelectedTaxonomies)"""
        if not self.current_book_id:
            messagebox.showinfo("Information", "Please select a book first")
            return
        
        # Validate required taxonomies
        genre_count = sum(1 for t in self.current_taxonomies if t.get("type") == "genre")
        theme_count = sum(1 for t in self.current_taxonomies if t.get("type") == "theme")
        trope_count = sum(1 for t in self.current_taxonomies if t.get("type") == "trope")
        
        missing = []
        if genre_count == 0:
            missing.append("at least 1 genre")
        if theme_count == 0:
            missing.append("at least 1 theme")
        if trope_count == 0:
            missing.append("at least 1 trope")
        
        if missing:
            messagebox.showerror("Error", f"Required taxonomies missing: {', '.join(missing)}")
            return
        
        # Find if this book already has taxonomies in memory
        found = False
        for i, relation in enumerate(self.parent.book_taxonomies):
            if isinstance(relation, dict) and relation.get("book_id") == self.current_book_id:
                # Update existing relation
                self.parent.book_taxonomies[i] = {
                    "book_id": self.current_book_id,
                    "taxonomies": self.current_taxonomies
                }
                found = True
                break
        
        if not found:
            # Add new relation
            self.parent.book_taxonomies.append({
                "book_id": self.current_book_id,
                "taxonomies": self.current_taxonomies
            })
        
        # Store in database if needed
        if hasattr(self.parent, 'db_manager'):
            try:
                # First delete existing associations
                self.parent.db_manager.execute_query(
                    "DELETE FROM book_genres WHERE book_id = ?", 
                    (self.current_book_id,)
                )
                
                # Then add new associations
                for taxonomy in self.current_taxonomies:
                    taxonomy_id = taxonomy.get("taxonomyId")
                    rank = taxonomy.get("rank", 0)
                    importance = float(self.selected_taxonomies.calculate_importance(rank))
                    
                    query = """
                    INSERT INTO book_genres (book_id, genre_id, rank, importance) 
                    VALUES (?, ?, ?, ?)
                    """
                    
                    self.parent.db_manager.execute_query(
                        query, 
                        (self.current_book_id, taxonomy_id, rank, importance)
                    )
                    
                messagebox.showinfo("Success", "Taxonomies saved successfully")
                
            except Exception as e:
                import app_logger as logger
                logger.log_error(f"Error saving taxonomies: {str(e)}")
                messagebox.showerror("Error", f"Failed to save taxonomies: {str(e)}")
        else:
            messagebox.showinfo("Success", "Taxonomies saved in memory")
        
        # Update parent if needed
        if hasattr(self.parent, 'update_export_status'):
            self.parent.update_export_status()
    
    def load_book_taxonomies(self, book_id):
        """
        Load taxonomies for a specific book
        
        Args:
            book_id: ID of the book to load taxonomies for
        """
        self.current_taxonomies = []
        
        # Try to load from database first for most up-to-date data
        if hasattr(self.parent, 'db_manager'):
            try:
                # Query the database for taxonomies
                query = """
                SELECT g.id, g.name, g.type, bg.rank, bg.importance
                FROM genres g
                JOIN book_genres bg ON g.id = bg.genre_id
                WHERE bg.book_id = ?
                ORDER BY bg.rank
                """
                
                results = self.parent.db_manager.execute_query(query, (book_id,))
                
                # Process results
                for i, result in enumerate(results):
                    taxonomy_id, name, tax_type, rank, importance = result
                    
                    # Use default type "genre" if not specified
                    if not tax_type:
                        tax_type = "genre"
                    
                    # Add to current taxonomies
                    self.current_taxonomies.append({
                        "taxonomyId": taxonomy_id,
                        "name": name,
                        "type": tax_type,
                        "rank": rank if rank is not None else i + 1
                    })
                    
                # If we found taxonomies in the database, return
                if self.current_taxonomies:
                    return
                    
            except Exception as e:
                import app_logger as logger
                logger.log_error(f"Error loading taxonomies from database: {str(e)}")
        
        # If database query failed or returned no results, try in-memory data
        for taxonomy_relation in self.parent.book_taxonomies:
            if isinstance(taxonomy_relation, dict) and taxonomy_relation.get("book_id") == book_id:
                self.current_taxonomies = taxonomy_relation.get("taxonomies", [])
                break
        
        # Sort by rank
        self.current_taxonomies.sort(key=lambda x: x.get("rank", 999))
    
    def update_taxonomy_counts(self):
        """Update the taxonomy tab labels with counts"""
        # Count taxonomies by type
        counts = {
            "genre": 0,
            "subgenre": 0,
            "theme": 0,
            "trope": 0
        }
        
        for taxonomy in self.current_taxonomies:
            tax_type = taxonomy.get("type", "")
            if tax_type in counts:
                counts[tax_type] += 1
        
        # Update tab labels
        self.taxonomy_selector.update_taxonomy_counts(counts)
    
    def import_genres_json(self):
        """Import genres from JSON"""
        # Ask for JSON file
        file_path = simpledialog.askstring(
            "Import Genres", 
            "Enter path to JSON file or paste JSON content:",
            parent=self.frame
        )
        
        if not file_path:
            return
            
        try:
            # Try to read as file path first
            try:
                with open(file_path, 'r') as f:
                    genres_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                # Try to parse as direct JSON content
                genres_data = json.loads(file_path)
                
            if not genres_data or not isinstance(genres_data, list):
                messagebox.showerror("Error", "Invalid JSON format. Expected an array of genre objects.")
                return
                
            # Import genres
            if hasattr(self.parent, 'data_sync') and hasattr(self.parent.data_sync, 'genre_processor'):
                result = self.parent.data_sync.genre_processor.import_genres_from_json(genres_data)
                
                if result:
                    messagebox.showinfo("Success", f"Successfully imported {len(genres_data)} genres")
                    # Update genre lists
                    self.taxonomy_selector.refresh_all_taxonomies()
                else:
                    messagebox.showerror("Error", "Failed to import genres")
            else:
                messagebox.showerror("Error", "Data synchronizer not available")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import genres: {str(e)}")
