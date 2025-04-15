import tkinter as tk
from tkinter import ttk, messagebox
import json
from csv_import_handler import CSVImportHandler
from tkinter import simpledialog

class GenresTab:
    def __init__(self, parent):
        self.parent = parent
        
        # Create tab
        self.frame = ttk.Frame(parent.notebook)
        parent.notebook.add(self.frame, text="Genres")
        
        # Initialize data structures
        if not hasattr(self.parent, 'book_taxonomies'):
            self.parent.book_taxonomies = []  # Will store book-taxonomy relationships
            
        self.current_book_id = None
        self.current_taxonomies = []
        
        # Dictionary to store taxonomy IDs for each list
        self.taxonomy_ids = {
            "genre": [],
            "subgenre": [],
            "theme": [],
            "trope": []
        }
        
        self.setup_tab()
        self.csv_import_handler = CSVImportHandler(self)
    
    def setup_tab(self):
        # Main split pane
        main_pane = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side - Book selection and taxonomy types
        left_frame = ttk.Frame(main_pane)
        main_pane.add(left_frame, weight=1)
        
        # Book selection
        book_frame = ttk.LabelFrame(left_frame, text="Book Selection")
        book_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(book_frame, text="Select a book:").pack(anchor=tk.W, padx=5, pady=2)
        self.book_var = tk.StringVar()
        self.book_combo = ttk.Combobox(book_frame, textvariable=self.book_var, width=30)
        self.book_combo.pack(fill=tk.X, padx=5, pady=2)
        self.book_combo.bind("<<ComboboxSelected>>", self.on_book_selected)
        
        # Taxonomy type tabs
        taxonomy_notebook = ttk.Notebook(left_frame)
        taxonomy_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Genre tab
        self.genre_frame = ttk.Frame(taxonomy_notebook)
        taxonomy_notebook.add(self.genre_frame, text="Genres (0/2)")
        
        # Subgenre tab
        self.subgenre_frame = ttk.Frame(taxonomy_notebook)
        taxonomy_notebook.add(self.subgenre_frame, text="Subgenres (0/5)")
        
        # Theme tab
        self.theme_frame = ttk.Frame(taxonomy_notebook)
        taxonomy_notebook.add(self.theme_frame, text="Themes (0/6)")
        
        # Trope tab
        self.trope_frame = ttk.Frame(taxonomy_notebook)
        taxonomy_notebook.add(self.trope_frame, text="Tropes (0/7)")
        
        # Set up each taxonomy type tab with search and selection
        self.setup_taxonomy_tab(self.genre_frame, "genre", 2)
        self.setup_taxonomy_tab(self.subgenre_frame, "subgenre", 5)
        self.setup_taxonomy_tab(self.theme_frame, "theme", 6)
        self.setup_taxonomy_tab(self.trope_frame, "trope", 7)
        
        # Right side - Selected taxonomies with reordering
        right_frame = ttk.LabelFrame(main_pane, text="Selected Taxonomies")
        main_pane.add(right_frame, weight=1)
        
        # Selected taxonomies label
        ttk.Label(right_frame, text="Drag and drop to reorder by importance:").pack(anchor=tk.W, padx=5, pady=2)
        
        # Selected taxonomies listbox with reordering
        self.selected_frame = ttk.Frame(right_frame)
        self.selected_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.selected_listbox = tk.Listbox(self.selected_frame, height=20, selectmode=tk.SINGLE)
        self.selected_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.selected_listbox.bind('<<ListboxSelect>>', self.on_selected_taxonomy_select)
        
        # Scrollbar for selected taxonomies
        selected_scrollbar = ttk.Scrollbar(self.selected_frame, orient=tk.VERTICAL, command=self.selected_listbox.yview)
        selected_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.selected_listbox.config(yscrollcommand=selected_scrollbar.set)
        
        # Buttons for reordering and removing
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Move Up", command=self.move_taxonomy_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Move Down", command=self.move_taxonomy_down).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Remove", command=self.remove_taxonomy).pack(side=tk.LEFT, padx=2)
        
        # Importance value display
        self.importance_var = tk.StringVar(value="Importance: N/A")
        ttk.Label(right_frame, textvariable=self.importance_var).pack(anchor=tk.W, padx=5, pady=2)
        
        # Save button
        ttk.Button(right_frame, text="Save Taxonomies", command=self.save_taxonomies).pack(fill=tk.X, padx=5, pady=10)
        
        # Import button for genres
        import_frame = ttk.Frame(self.frame)
        import_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(import_frame, text="Import Genres from JSON", command=self.import_genres_json).pack(side=tk.LEFT, padx=5)
    
    def setup_taxonomy_tab(self, frame, taxonomy_type, max_count):
        """Set up a tab for a specific taxonomy type"""
        # Search frame
        search_frame = ttk.Frame(frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(search_frame, text=f"Search {taxonomy_type}s:").pack(side=tk.LEFT, padx=2)
        
        search_var = tk.StringVar()
        search_var.trace_add("write", lambda *args: self.filter_taxonomies(taxonomy_type, search_var.get()))
        search_entry = ttk.Entry(search_frame, textvariable=search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # Label with instruction
        ttk.Label(frame, text=f"Select up to {max_count} {taxonomy_type}s:").pack(anchor=tk.W, padx=5, pady=2)
        
        # Listbox frame
        listbox_frame = ttk.Frame(frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Taxonomy listbox with scrollbar
        taxonomy_listbox = tk.Listbox(listbox_frame, height=15, selectmode=tk.SINGLE)
        taxonomy_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind double-click to add taxonomy
        taxonomy_listbox.bind("<Double-1>", lambda event: self.add_taxonomy(taxonomy_type))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=taxonomy_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        taxonomy_listbox.config(yscrollcommand=scrollbar.set)
        
        # Add button
        ttk.Button(frame, text=f"Add Selected {taxonomy_type.capitalize()}", 
                 command=lambda: self.add_taxonomy(taxonomy_type)).pack(fill=tk.X, padx=5, pady=5)
        
        # Store references to widgets
        setattr(self, f"{taxonomy_type}_listbox", taxonomy_listbox)
        setattr(self, f"{taxonomy_type}_search", search_var)
    
    def update_genre_book_dropdown(self):
        """Update book selection dropdown in genres tab"""
        book_titles = []
        book_ids = []
        
        for book in self.parent.books:
            if isinstance(book, dict):
                book_titles.append(book.get("title", ""))
                book_ids.append(book.get("id", ""))
        
        self.book_combo['values'] = book_titles
        self.book_ids = book_ids
        
        # Populate all taxonomy lists
        self.populate_all_taxonomy_lists()
    
    def on_book_selected(self, event):
        """Handle book selection"""
        book_name = self.book_var.get()
        if not book_name:
            return
        
        # Find book ID
        book_id = None
        for i, book in enumerate(self.parent.books):
            if isinstance(book, dict) and book.get("title") == book_name:
                book_id = book.get("id")
                break
        
        if book_id is None:
            messagebox.showerror("Error", f"Book '{book_name}' not found in database")
            return
        
        self.current_book_id = book_id
        
        # Load taxonomies for this book
        self.load_book_taxonomies(book_id)
        
        # Update UI
        self.update_selected_listbox()
        self.update_taxonomy_tabs()
        self.update_taxonomy_lists_with_selections()
    
    def load_book_taxonomies(self, book_id):
        """Load taxonomies for a specific book"""
        self.current_taxonomies = []
        
        # Find taxonomies for this book in the parent's book_taxonomies
        for taxonomy_relation in self.parent.book_taxonomies:
            if isinstance(taxonomy_relation, dict) and taxonomy_relation.get("book_id") == book_id:
                self.current_taxonomies = taxonomy_relation.get("taxonomies", [])
                break
        
        # Sort by rank
        self.current_taxonomies.sort(key=lambda x: x.get("rank", 999))
    
    def filter_taxonomies(self, taxonomy_type, search_text):
        """Filter taxonomies based on search text"""
        listbox = getattr(self, f"{taxonomy_type}_listbox")
        listbox.delete(0, tk.END)
        
        # Clear the stored IDs for this taxonomy type
        self.taxonomy_ids[taxonomy_type] = []
        
        search_text = search_text.lower()
        
        # Get all taxonomies of this type
        taxonomies = self.get_taxonomies_by_type(taxonomy_type)
        
        # Filter based on search and exclude already selected ones
        for taxonomy in taxonomies:
            name = taxonomy.get("name", "").lower()
            description = taxonomy.get("description", "").lower()
            
            # Check if already selected
            taxonomy_id = taxonomy.get("id")
            already_selected = any(
                t.get("taxonomyId") == taxonomy_id and t.get("type") == taxonomy_type
                for t in self.current_taxonomies
            )
            
            if ((not search_text or search_text in name or search_text in description) and 
                not already_selected):
                display_text = f"{taxonomy.get('name')} - {taxonomy.get('description', '')[:30]}..."
                listbox.insert(tk.END, display_text)
                
                # Store the ID in our parallel list
                self.taxonomy_ids[taxonomy_type].append(taxonomy_id)
    
    def populate_all_taxonomy_lists(self):
        """Populate all taxonomy lists initially"""
        for taxonomy_type in ["genre", "subgenre", "theme", "trope"]:
            self.filter_taxonomies(taxonomy_type, "")
    
    def update_taxonomy_lists_with_selections(self):
        """Update taxonomy lists to exclude selected items"""
        for taxonomy_type in ["genre", "subgenre", "theme", "trope"]:
            self.filter_taxonomies(taxonomy_type, getattr(self, f"{taxonomy_type}_search").get())
    
    def get_taxonomies_by_type(self, taxonomy_type):
        """Get all taxonomies of a specific type"""
        # In a real implementation, this would fetch from the database
        # For now we'll use the parent's genres as a placeholder
        if not hasattr(self.parent, 'genres'):
            return []
            
        taxonomies = []
        for genre in self.parent.genres:
            if isinstance(genre, dict) and genre.get("type", "genre") == taxonomy_type:
                taxonomies.append(genre)
        
        return taxonomies
    
    def add_taxonomy(self, taxonomy_type):
        """Add a taxonomy to the selected list"""
        listbox = getattr(self, f"{taxonomy_type}_listbox")
        selected_indices = listbox.curselection()
        
        if not selected_indices:
            messagebox.showinfo("Information", f"Please select a {taxonomy_type} first")
            return
        
        index = selected_indices[0]
        
        # Get the taxonomy ID from our stored list
        if index >= len(self.taxonomy_ids[taxonomy_type]):
            messagebox.showerror("Error", f"Could not determine {taxonomy_type} ID")
            return
            
        taxonomy_id = self.taxonomy_ids[taxonomy_type][index]
        
        # Get the taxonomy info
        taxonomy_info = None
        for taxonomy in self.get_taxonomies_by_type(taxonomy_type):
            if taxonomy.get("id") == taxonomy_id:
                taxonomy_info = taxonomy
                break
        
        if not taxonomy_info:
            messagebox.showerror("Error", f"{taxonomy_type.capitalize()} not found in database")
            return
        
        # Check if we've reached the maximum for this type
        type_count = sum(1 for t in self.current_taxonomies if t.get("type") == taxonomy_type)
        max_counts = {"genre": 2, "subgenre": 5, "theme": 6, "trope": 7}
        
        if type_count >= max_counts.get(taxonomy_type, 0):
            messagebox.showinfo("Information", 
                              f"Maximum of {max_counts.get(taxonomy_type)} {taxonomy_type}s already selected")
            return
        
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
        self.update_selected_listbox()
        self.update_taxonomy_tabs()
        self.update_taxonomy_lists_with_selections()
    
    def remove_taxonomy(self):
        """Remove the selected taxonomy"""
        selected_indices = self.selected_listbox.curselection()
        
        if not selected_indices:
            messagebox.showinfo("Information", "Please select a taxonomy to remove")
            return
        
        index = selected_indices[0]
        if index < len(self.current_taxonomies):
            removed = self.current_taxonomies.pop(index)
            
            # Reorder ranks
            for i, taxonomy in enumerate(self.current_taxonomies):
                taxonomy["rank"] = i + 1
            
            # Update UI
            self.update_selected_listbox()
            self.update_taxonomy_tabs()
            self.update_taxonomy_lists_with_selections()
    
    def move_taxonomy_up(self):
        """Move the selected taxonomy up in rank"""
        selected_indices = self.selected_listbox.curselection()
        
        if not selected_indices:
            messagebox.showinfo("Information", "Please select a taxonomy to move")
            return
        
        index = selected_indices[0]
        if index > 0 and index < len(self.current_taxonomies):
            # Swap with previous
            self.current_taxonomies[index], self.current_taxonomies[index-1] = \
                self.current_taxonomies[index-1], self.current_taxonomies[index]
            
            # Update ranks
            for i, taxonomy in enumerate(self.current_taxonomies):
                taxonomy["rank"] = i + 1
            
            # Update UI
            self.update_selected_listbox()
            self.selected_listbox.selection_set(index-1)
    
    def move_taxonomy_down(self):
        """Move the selected taxonomy down in rank"""
        selected_indices = self.selected_listbox.curselection()
        
        if not selected_indices:
            messagebox.showinfo("Information", "Please select a taxonomy to move")
            return
        
        index = selected_indices[0]
        if index < len(self.current_taxonomies) - 1:
            # Swap with next
            self.current_taxonomies[index], self.current_taxonomies[index+1] = \
                self.current_taxonomies[index+1], self.current_taxonomies[index]
            
            # Update ranks
            for i, taxonomy in enumerate(self.current_taxonomies):
                taxonomy["rank"] = i + 1
            
            # Update UI
            self.update_selected_listbox()
            self.selected_listbox.selection_set(index+1)
    
    def update_selected_listbox(self):
        """Update the selected taxonomies listbox"""
        self.selected_listbox.delete(0, tk.END)
        
        for taxonomy in self.current_taxonomies:
            rank = taxonomy.get("rank", 0)
            name = taxonomy.get("name", "")
            tax_type = taxonomy.get("type", "")
            importance = self.calculate_importance(rank)
            
            display_text = f"[{tax_type.upper()}] {name} (Rank: {rank}, Imp: {importance})"
            self.selected_listbox.insert(tk.END, display_text)
    
    def update_taxonomy_tabs(self):
        """Update the tab labels with counts"""
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
        max_counts = {"genre": 2, "subgenre": 5, "theme": 6, "trope": 7}
        
        # Get the notebook widget that contains our taxonomy tabs
        taxonomy_notebook = self.genre_frame.master
        
        for i, tax_type in enumerate(["genre", "subgenre", "theme", "trope"]):
            max_count = max_counts.get(tax_type, 0)
            count = counts.get(tax_type, 0)
            
            # Update the notebook tab text - using the index to get the correct tab
            taxonomy_notebook.tab(i, text=f"{tax_type.capitalize()}s ({count}/{max_count})")
    
    def calculate_importance(self, rank):
        """Calculate importance value based on rank"""
        if rank <= 0:
            return "0.000"
        return f"{(1 / (1 + 0.3 * (rank - 1))):.3f}"
    
    def on_selected_taxonomy_select(self, event):
        """Handle selection in the selected taxonomies listbox"""
        selected_indices = self.selected_listbox.curselection()
        
        if not selected_indices:
            self.importance_var.set("Importance: N/A")
            return
        
        index = selected_indices[0]
        if index < len(self.current_taxonomies):
            taxonomy = self.current_taxonomies[index]
            rank = taxonomy.get("rank", 0)
            importance = self.calculate_importance(rank)
            
            self.importance_var.set(f"Importance: {importance}")
    
    def save_taxonomies(self):
        """Save the current taxonomies for the selected book"""
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
                self.parent.db_manager.add_book_genre(
                    self.current_book_id,
                    taxonomy.get("taxonomyId"),
                    None  # Relation ID (auto-generated)
                )
        
        messagebox.showinfo("Success", "Taxonomies saved successfully")
        
        # Update parent if needed
        if hasattr(self.parent, 'update_export_status'):
            self.parent.update_export_status()
    
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
            if hasattr(self.parent, 'data_sync'):
                result = self.parent.data_sync.import_genres_from_json(genres_data)
                
                if result:
                    messagebox.showinfo("Success", f"Successfully imported {len(genres_data)} genres")
                    # Update genre lists
                    self.populate_all_taxonomy_lists()
                else:
                    messagebox.showerror("Error", "Failed to import genres")
            else:
                messagebox.showerror("Error", "Data synchronizer not available")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import genres: {str(e)}")
