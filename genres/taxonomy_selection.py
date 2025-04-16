import tkinter as tk
from tkinter import ttk, messagebox

class TaxonomySelector:
    def __init__(self, parent_frame, parent_controller):
        """
        Initialize the taxonomy selection component
        
        Args:
            parent_frame: The parent tkinter frame where this component will be placed
            parent_controller: The controller class that manages communication between components
        """
        self.parent = parent_controller
        self.frame = ttk.Frame(parent_frame)
        
        # Dictionary to store taxonomy IDs for each list
        self.taxonomy_ids = {
            "genre": [],
            "subgenre": [],
            "theme": [],
            "trope": []
        }
        
        # Maximum counts for each taxonomy type
        self.max_counts = {
            "genre": 2,
            "subgenre": 5,
            "theme": 6,
            "trope": 7
        }
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI components for taxonomy selection"""
        # Create notebook with tabs for each taxonomy type
        self.taxonomy_notebook = ttk.Notebook(self.frame)
        self.taxonomy_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create frames for each taxonomy type
        self.genre_frame = ttk.Frame(self.taxonomy_notebook)
        self.subgenre_frame = ttk.Frame(self.taxonomy_notebook)
        self.theme_frame = ttk.Frame(self.taxonomy_notebook)
        self.trope_frame = ttk.Frame(self.taxonomy_notebook)
        
        # Add frames to notebook
        self.taxonomy_notebook.add(self.genre_frame, text="Genres (0/2)")
        self.taxonomy_notebook.add(self.subgenre_frame, text="Subgenres (0/5)")
        self.taxonomy_notebook.add(self.theme_frame, text="Themes (0/6)")
        self.taxonomy_notebook.add(self.trope_frame, text="Tropes (0/7)")
        
        # Set up each taxonomy type tab
        self.setup_taxonomy_tab(self.genre_frame, "genre", self.max_counts["genre"])
        self.setup_taxonomy_tab(self.subgenre_frame, "subgenre", self.max_counts["subgenre"])
        self.setup_taxonomy_tab(self.theme_frame, "theme", self.max_counts["theme"])
        self.setup_taxonomy_tab(self.trope_frame, "trope", self.max_counts["trope"])
    
    def setup_taxonomy_tab(self, frame, taxonomy_type, max_count):
        """
        Set up a tab for a specific taxonomy type
        
        Args:
            frame: The frame where components will be placed
            taxonomy_type: Type of taxonomy (genre, subgenre, theme, trope)
            max_count: Maximum number of taxonomies that can be selected
        """
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
    
    def filter_taxonomies(self, taxonomy_type, search_text):
        """
        Filter taxonomies based on search text
        
        Args:
            taxonomy_type: Type of taxonomy to filter
            search_text: Text to search for
        """
        listbox = getattr(self, f"{taxonomy_type}_listbox")
        listbox.delete(0, tk.END)
        
        # Clear the stored IDs for this taxonomy type
        self.taxonomy_ids[taxonomy_type] = []
        
        search_text = search_text.lower()
        
        # Get all taxonomies of this type
        taxonomies = self.parent.get_taxonomies_by_type(taxonomy_type)
        
        # Get current selected taxonomies
        current_taxonomies = self.parent.get_current_taxonomies()
        
        # Filter based on search and exclude already selected ones
        for taxonomy in taxonomies:
            name = taxonomy.get("name", "").lower()
            description = taxonomy.get("description", "").lower()
            
            # Check if already selected
            taxonomy_id = taxonomy.get("id")
            already_selected = any(
                t.get("taxonomyId") == taxonomy_id and t.get("type") == taxonomy_type
                for t in current_taxonomies
            )
            
            if ((not search_text or search_text in name or search_text in description) and 
                not already_selected):
                display_text = f"{taxonomy.get('name')} - {taxonomy.get('description', '')[:30]}..."
                listbox.insert(tk.END, display_text)
                
                # Store the ID in our parallel list
                self.taxonomy_ids[taxonomy_type].append(taxonomy_id)
    
    def add_taxonomy(self, taxonomy_type):
        """
        Add a taxonomy to the selected list
        
        Args:
            taxonomy_type: Type of taxonomy to add
        """
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
        
        # Ask parent to add the taxonomy and check if successful
        success = self.parent.add_taxonomy(taxonomy_type, taxonomy_id)
        
        if success:
            # Refresh taxonomies to exclude the newly added one
            self.filter_taxonomies(taxonomy_type, getattr(self, f"{taxonomy_type}_search").get())
    
    def update_taxonomy_counts(self, counts):
        """
        Update the tab labels with counts
        
        Args:
            counts: Dictionary with counts for each taxonomy type
        """
        for i, tax_type in enumerate(["genre", "subgenre", "theme", "trope"]):
            max_count = self.max_counts.get(tax_type, 0)
            count = counts.get(tax_type, 0)
            
            # Update the notebook tab text
            self.taxonomy_notebook.tab(i, text=f"{tax_type.capitalize()}s ({count}/{max_count})")
    
    def refresh_all_taxonomies(self):
        """Refresh all taxonomy lists"""
        for taxonomy_type in ["genre", "subgenre", "theme", "trope"]:
            self.filter_taxonomies(taxonomy_type, getattr(self, f"{taxonomy_type}_search").get())
    
    def get_frame(self):
        """Return the main frame of this component"""
        return self.frame
