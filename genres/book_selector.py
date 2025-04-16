import tkinter as tk
from tkinter import ttk, messagebox

class BookSelector:
    def __init__(self, parent_frame, parent_controller):
        """
        Initialize the book selection component
        
        Args:
            parent_frame: The parent tkinter frame where this component will be placed
            parent_controller: The controller class that manages communication between components
        """
        self.parent = parent_controller
        self.frame = ttk.LabelFrame(parent_frame, text="Book Selection")
        
        # Book data
        self.book_ids = []
        self.books_data = []
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI components for book selection"""
        # Book search 
        search_frame = ttk.Frame(self.frame)
        search_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(search_frame, text="Search book:").pack(side=tk.LEFT, padx=2)
        
        self.book_search_var = tk.StringVar()
        self.book_search_var.trace_add("write", lambda *args: self.filter_books(self.book_search_var.get()))
        book_search_entry = ttk.Entry(search_frame, textvariable=self.book_search_var)
        book_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        ttk.Label(self.frame, text="Select a book:").pack(anchor=tk.W, padx=5, pady=2)
        
        # Book listbox with scrollbar
        book_list_frame = ttk.Frame(self.frame)
        book_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.book_listbox = tk.Listbox(book_list_frame, height=8, selectmode=tk.SINGLE)
        self.book_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.book_listbox.bind("<<ListboxSelect>>", self.on_book_select)
        
        book_scrollbar = ttk.Scrollbar(book_list_frame, orient=tk.VERTICAL, command=self.book_listbox.yview)
        book_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.book_listbox.config(yscrollcommand=book_scrollbar.set)
        
        # Keep the original combobox for backward compatibility
        self.book_var = tk.StringVar()
        self.book_combo = ttk.Combobox(self.frame, textvariable=self.book_var, width=30)
        self.book_combo.pack(fill=tk.X, padx=5, pady=2)
        self.book_combo.bind("<<ComboboxSelected>>", self.on_combobox_select)
    
    def filter_books(self, search_text):
        """
        Filter books based on search text
        
        Args:
            search_text: Text to search for in book titles and authors
        """
        self.book_listbox.delete(0, tk.END)
        self.book_ids = []
        
        search_text = search_text.lower()
        
        # Filter books based on search
        for book in self.books_data:
            title = book.get("title", "").lower()
            author = book.get("author", "").lower()
            
            if not search_text or search_text in title or search_text in author:
                display_text = f"{book.get('title')} - {book.get('author', '')}"
                self.book_listbox.insert(tk.END, display_text)
                self.book_ids.append(book.get("id"))
    
    def on_book_select(self, event):
        """Handle book selection from listbox"""
        selected_indices = self.book_listbox.curselection()
        
        if not selected_indices:
            return
        
        index = selected_indices[0]
        
        # Get the book ID from our stored list
        if index >= len(self.book_ids):
            return
            
        book_id = self.book_ids[index]
        
        # Get the book info
        book_info = None
        for book in self.books_data:
            if book.get("id") == book_id:
                book_info = book
                break
        
        if not book_info:
            return
        
        # Set the book in the combobox for consistency
        self.book_var.set(book_info.get("title", ""))
        
        # Notify the parent controller about book selection
        self.parent.on_book_selected(book_id)
    
    def on_combobox_select(self, event):
        """Handle book selection from combobox"""
        book_name = self.book_var.get()
        if not book_name:
            return
        
        # Find book ID
        book_id = None
        for book in self.books_data:
            if isinstance(book, dict) and book.get("title") == book_name:
                book_id = book.get("id")
                
                # Also select in listbox for consistency
                try:
                    listbox_index = self.book_ids.index(book_id)
                    self.book_listbox.selection_clear(0, tk.END)
                    self.book_listbox.selection_set(listbox_index)
                    self.book_listbox.see(listbox_index)
                except (ValueError, IndexError):
                    pass
                
                break
        
        if book_id is None:
            messagebox.showerror("Error", f"Book '{book_name}' not found in database")
            return
        
        # Notify the parent controller about book selection
        self.parent.on_book_selected(book_id)
    
    def update_books(self, books_data):
        """
        Update the books data and refresh display
        
        Args:
            books_data: List of book dictionaries
        """
        self.books_data = books_data
        
        # Update combobox values
        book_titles = [book.get("title", "") for book in books_data if isinstance(book, dict)]
        self.book_combo['values'] = book_titles
        
        # Refresh search/filter
        self.filter_books(self.book_search_var.get())
    
    def select_book_by_id(self, book_id):
        """
        Programmatically select a book by ID
        
        Args:
            book_id: ID of the book to select
        """
        # Find book in data
        book_info = None
        for book in self.books_data:
            if book.get("id") == book_id:
                book_info = book
                break
        
        if not book_info:
            return False
        
        # Update combobox
        self.book_var.set(book_info.get("title", ""))
        
        # Update listbox selection
        try:
            listbox_index = self.book_ids.index(book_id)
            self.book_listbox.selection_clear(0, tk.END)
            self.book_listbox.selection_set(listbox_index)
            self.book_listbox.see(listbox_index)
        except (ValueError, IndexError):
            pass
        
        return True
    
    def get_frame(self):
        """Return the main frame of this component"""
        return self.frame
