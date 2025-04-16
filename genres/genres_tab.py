import tkinter as tk
from tkinter import ttk, messagebox
import json
from csv_import_handler import CSVImportHandler
from tkinter import simpledialog

# Import component modules
from .book_selector import BookSelector
from .taxonomy_selection import TaxonomySelector
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
        
        for book in self.parent.books:
            if isinstance(book, dict):
                books_data.append(book)
        
        # Update book selector with books data
        self.book_selector.update_books(books_data)
        
        # Populate all taxonomy lists
        self.taxonomy_selector.refresh_all_taxonomies()
    
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
        
        # Update UI
        self.selected_taxonomies.update_selected_listbox(self.current_taxonomies)
        self.update_taxonomy_counts()
        self.taxonomy_selector.refresh_all_taxonomies()
    
    def get_taxonomies_by_type(self, taxonomy_type):
        """
        Get all taxonomies of a specific type (called by TaxonomySelector)
        
        Args:
            taxonomy_type: Type of taxonomy to get
            
        Returns:
            List of taxonomy dictionaries
        """
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
        
        # Find if this book already has taxonomies
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
            # For each taxonomy, store book_id, taxonomy_id, type, and rank
            self.parent.db_manager.execute_query(
                "DELETE FROM book_genres WHERE book_id = ?", 
                (self.current_book_id,)
            )
            
            for taxonomy in self.current_taxonomies:
                taxonomy_id = taxonomy.get("taxonomyId")
                rank = taxonomy.get("rank", 0)
                importance = float(self.selected_taxonomies.calculate_importance(rank))
                
                query = """
                INSERT INTO book_genres (book_id, genre_id, rank, importance) 
                VALUES (?, ?, ?, ?)
                """
                
                try:
                    self.parent.db_manager.execute_query(
                        query, 
                        (self.current_book_id, taxonomy_id, rank, importance)
                    )
                except Exception as e:
                    import app_logger as logger
                    logger.log_error(f"Error saving taxonomy {taxonomy_id}: {str(e)}")
        
        messagebox.showinfo("Success", "Taxonomies saved successfully")
        
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
        
        # Find taxonomies for this book in the parent's book_taxonomies
        for taxonomy_relation in self.parent.book_taxonomies:
            if isinstance(taxonomy_relation, dict) and taxonomy_relation.get("book_id") == book_id:
                self.current_taxonomies = taxonomy_relation.get("taxonomies", [])
                break
                
        # If book_taxonomies is empty or book not found, try to load from database
        if not self.current_taxonomies and hasattr(self.parent, 'db_manager'):
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
                    
                    # Add to current taxonomies
                    self.current_taxonomies.append({
                        "taxonomyId": taxonomy_id,
                        "name": name,
                        "type": tax_type if tax_type else "genre",
                        "rank": rank if rank is not None else i + 1
                    })
            except Exception as e:
                import app_logger as logger
                logger.log_error(f"Error loading taxonomies from database: {str(e)}")
        
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
