import tkinter as tk
from tkinter import ttk, messagebox

class SelectedTaxonomies:
    def __init__(self, parent_frame, parent_controller):
        """
        Initialize the selected taxonomies component
        
        Args:
            parent_frame: The parent tkinter frame where this component will be placed
            parent_controller: The controller class that manages communication between components
        """
        self.parent = parent_controller
        self.frame = ttk.LabelFrame(parent_frame, text="Selected Taxonomies")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI components for selected taxonomies"""
        # Selected taxonomies label
        ttk.Label(self.frame, text="Drag and drop to reorder by importance:").pack(anchor=tk.W, padx=5, pady=2)
        
        # Selected taxonomies listbox with reordering
        self.selected_frame = ttk.Frame(self.frame)
        self.selected_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.selected_listbox = tk.Listbox(self.selected_frame, height=20, selectmode=tk.SINGLE)
        self.selected_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.selected_listbox.bind('<<ListboxSelect>>', self.on_selected_taxonomy_select)
        
        # Scrollbar for selected taxonomies
        selected_scrollbar = ttk.Scrollbar(self.selected_frame, orient=tk.VERTICAL, command=self.selected_listbox.yview)
        selected_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.selected_listbox.config(yscrollcommand=selected_scrollbar.set)
        
        # Buttons for reordering and removing
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Move Up", command=self.move_taxonomy_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Move Down", command=self.move_taxonomy_down).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Remove", command=self.remove_taxonomy).pack(side=tk.LEFT, padx=2)
        
        # Importance value display
        self.importance_var = tk.StringVar(value="Importance: N/A")
        ttk.Label(self.frame, textvariable=self.importance_var).pack(anchor=tk.W, padx=5, pady=2)
        
        # Save button
        ttk.Button(self.frame, text="Save Taxonomies", command=self.save_taxonomies).pack(fill=tk.X, padx=5, pady=10)
    
    def update_selected_listbox(self, taxonomies):
        """
        Update the selected taxonomies listbox
        
        Args:
            taxonomies: List of taxonomy dictionaries
        """
        self.selected_listbox.delete(0, tk.END)
        
        for taxonomy in taxonomies:
            rank = taxonomy.get("rank", 0)
            name = taxonomy.get("name", "")
            tax_type = taxonomy.get("type", "")
            importance = self.calculate_importance(rank)
            
            display_text = f"[{tax_type.upper()}] {name} (Rank: {rank}, Imp: {importance})"
            self.selected_listbox.insert(tk.END, display_text)
    
    def calculate_importance(self, rank):
        """
        Calculate importance value based on rank
        
        Args:
            rank: The rank value
            
        Returns:
            Formatted importance value
        """
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
        current_taxonomies = self.parent.get_current_taxonomies()
        
        if index < len(current_taxonomies):
            taxonomy = current_taxonomies[index]
            rank = taxonomy.get("rank", 0)
            importance = self.calculate_importance(rank)
            
            self.importance_var.set(f"Importance: {importance}")
    
    def move_taxonomy_up(self):
        """Move the selected taxonomy up in rank"""
        selected_indices = self.selected_listbox.curselection()
        
        if not selected_indices:
            messagebox.showinfo("Information", "Please select a taxonomy to move")
            return
        
        index = selected_indices[0]
        self.parent.move_taxonomy(index, "up")
        
        # Update selection
        if index > 0:
            self.selected_listbox.selection_set(index-1)
    
    def move_taxonomy_down(self):
        """Move the selected taxonomy down in rank"""
        selected_indices = self.selected_listbox.curselection()
        
        if not selected_indices:
            messagebox.showinfo("Information", "Please select a taxonomy to move")
            return
        
        index = selected_indices[0]
        self.parent.move_taxonomy(index, "down")
        
        # Update selection
        current_taxonomies = self.parent.get_current_taxonomies()
        if index < len(current_taxonomies) - 1:
            self.selected_listbox.selection_set(index+1)
    
    def remove_taxonomy(self):
        """Remove the selected taxonomy"""
        selected_indices = self.selected_listbox.curselection()
        
        if not selected_indices:
            messagebox.showinfo("Information", "Please select a taxonomy to remove")
            return
        
        index = selected_indices[0]
        self.parent.remove_taxonomy(index)
    
    def save_taxonomies(self):
        """Save the current taxonomies"""
        self.parent.save_taxonomies()
    
    def get_frame(self):
        """Return the main frame of this component"""
        return self.frame
