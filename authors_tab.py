import tkinter as tk
import os
from tkinter import ttk, messagebox
import requests
from PIL import Image, ImageTk
from io import BytesIO
import json
from csv_import_handler import CSVImportHandler

class AuthorsTab:
    def __init__(self, parent):
        self.parent = parent
        self.db_manager = parent.db_manager
        
        # Create tab
        self.frame = ttk.Frame(parent.notebook)
        parent.notebook.add(self.frame, text="Authors")
        
        self.setup_tab()
        self.csv_import_handler = CSVImportHandler(self)
        
        # Initial population of author list
        self.update_authors_listbox()
    
    def setup_tab(self):
        # Main container frame
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Author list frame (left side)
        authors_list_frame = ttk.Frame(main_frame)
        authors_list_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10), pady=10)
        
        # Author list
        ttk.Label(authors_list_frame, text="Authors:").pack(anchor=tk.W)
        self.authors_listbox = tk.Listbox(authors_list_frame, width=30, height=20)
        self.authors_listbox.pack(fill=tk.BOTH, expand=True)
        self.authors_listbox.bind('<<ListboxSelect>>', self.on_author_select)
        
        # Buttons for author management
        btn_frame = ttk.Frame(authors_list_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Add New", command=self.add_author).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete", command=self.delete_author).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Refresh", command=self.update_authors_listbox).pack(side=tk.LEFT, padx=5)
        
        # Right side container
        right_container = ttk.Frame(main_frame)
        right_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Top row frame for details and image preview side by side
        top_row = ttk.Frame(right_container)
        top_row.pack(fill=tk.X, pady=(0, 10))
        
        # Author fields frame (left side of top row)
        fields_frame = ttk.Frame(top_row)
        fields_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Author ID (hidden field)
        self.author_id_var = tk.StringVar()
        
        # User ID association
        ttk.Label(fields_frame, text="User ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.user_id_var = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=self.user_id_var, width=40).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Author name
        ttk.Label(fields_frame, text="Author Name*:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.author_name_var = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=self.author_name_var, width=40).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Author image URL
        ttk.Label(fields_frame, text="Author Image URL:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.author_image_url_var = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=self.author_image_url_var, width=40).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Birth date
        ttk.Label(fields_frame, text="Birth Date (YYYY-MM-DD):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.birth_date_var = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=self.birth_date_var, width=40).grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Death date
        ttk.Label(fields_frame, text="Death Date (YYYY-MM-DD):").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.death_date_var = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=self.death_date_var, width=40).grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # Preview frame for author image (moved to right side of top row)
        preview_frame = ttk.LabelFrame(top_row, text="Profile Pic Preview")
        preview_frame.pack(side=tk.RIGHT, padx=(0, 5), pady=5, anchor=tk.N)
        
        self.author_image_preview = ttk.Label(preview_frame)
        self.author_image_preview.pack(pady=5, padx=5)
        
        
        # Bottom of fields frame
        bottom_fields = ttk.Frame(right_container)
        bottom_fields.pack(fill=tk.BOTH, expand=True)
        
        # Website
        ttk.Label(fields_frame, text="Website:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.website_var = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=self.website_var, width=40).grid(row=5, column=1, sticky=tk.W, pady=5)
        
        # Bio
        ttk.Label(fields_frame, text="Bio:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.bio_text = tk.Text(fields_frame, width=40, height=5)
        self.bio_text.grid(row=6, column=1, sticky=tk.W, pady=5)
        
        # Save button
        ttk.Button(bottom_fields, text="Save Author", command=self.save_author).grid(
            row=2, column=0, columnspan=2, pady=10
        )
        
        # Author books frame
        author_books_frame = ttk.LabelFrame(right_container, text="Author's Books")
        author_books_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.books_listbox = tk.Listbox(author_books_frame, height=6)
        self.books_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure grid weights
        fields_frame.columnconfigure(1, weight=1)
        bottom_fields.columnconfigure(1, weight=1)    
        

    def add_author(self):
        """Add a new author to the list"""
        self.clear_author_fields()
        # Clear the ID to indicate this is a new author
        self.author_id_var.set("")
    
    def save_author(self):
        """Save current author data"""
        author_name = self.author_name_var.get().strip()
        
        if not author_name:
            messagebox.showerror("Error", "Author name is required")
            return
        
        # Get current author data
        author_data = {
            "userId": self.user_id_var.get().strip() or None,
            "author_name": author_name,
            "author_image_url": self.author_image_url_var.get().strip(),
            "birth_date": self.birth_date_var.get().strip(),
            "death_date": self.death_date_var.get().strip(),
            "website": self.website_var.get().strip(),
            "bio": self.bio_text.get("1.0", tk.END).strip()
        }
        
        try:
            author_id = self.author_id_var.get().strip()
            
            if author_id:  # Update existing author
                # Update author data
                query = """
                UPDATE authors SET
                    userId = ?,
                    author_name = ?,
                    author_image_url = ?,
                    birth_date = ?,
                    death_date = ?,
                    website = ?,
                    bio = ?
                WHERE id = ?
                """
                params = (
                    author_data["userId"],
                    author_data["author_name"],
                    author_data["author_image_url"],
                    author_data["birth_date"],
                    author_data["death_date"],
                    author_data["website"],
                    author_data["bio"],
                    author_id
                )
                self.db_manager.execute_query(query, params)
                messagebox.showinfo("Success", f"Author '{author_name}' updated successfully")
            else:  # Add new author
                # Generate new ID - in a real app, we might let the DB auto-increment
                query = "SELECT MAX(id) FROM authors"
                result = self.db_manager.execute_query(query)
                new_id = 1
                if result and result[0][0] is not None:
                    new_id = result[0][0] + 1
                
                author_data["id"] = new_id
                self.db_manager.add_author(author_data)
                messagebox.showinfo("Success", f"Author '{author_name}' added successfully")
            
            # Update UI
            self.update_authors_listbox()
            if hasattr(self.parent, 'books_tab'):
                self.parent.books_tab.update_book_author_dropdown()
            if hasattr(self.parent, 'images_tab'):
                self.parent.images_tab.update_image_item_dropdown()
            if hasattr(self.parent, 'update_export_status'):
                self.parent.update_export_status()
                
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to save author: {str(e)}")
    
    def delete_author(self):
        """Delete the selected author"""
        selected_indices = self.authors_listbox.curselection()
        
        if not selected_indices:
            messagebox.showerror("Error", "No author selected")
            return
        
        index = selected_indices[0]
        authors = self.get_authors_from_db()
        
        if index < len(authors):
            author = authors[index]
            author_id = author[0]  # ID is the first column
            author_name = author[2]  # author_name is the third column
            
            # Check if author is used in any books
            books = self.db_manager.get_books_by_author(author_id)
            if books:
                messagebox.showerror(
                    "Error", 
                    f"Cannot delete author '{author_name}' because they are assigned to one or more books"
                )
                return
            
            # Confirm deletion
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete author '{author_name}'?"):
                try:
                    # Delete author
                    query = "DELETE FROM authors WHERE id = ?"
                    self.db_manager.execute_query(query, (author_id,))
                    
                    # Update UI
                    self.update_authors_listbox()
                    self.clear_author_fields()
                    if hasattr(self.parent, 'books_tab'):
                        self.parent.books_tab.update_book_author_dropdown()
                    if hasattr(self.parent, 'images_tab'):
                        self.parent.images_tab.update_image_item_dropdown()
                    if hasattr(self.parent, 'update_export_status'):
                        self.parent.update_export_status()
                        
                    messagebox.showinfo("Success", f"Author '{author_name}' deleted successfully")
                except Exception as e:
                    messagebox.showerror("Database Error", f"Failed to delete author: {str(e)}")
    
    def on_author_select(self, event):
        """Handle author selection"""
        selected_indices = self.authors_listbox.curselection()
        
        if not selected_indices:
            return
        
        index = selected_indices[0]
        authors = self.get_authors_from_db()
        
        if index < len(authors):
            author = authors[index]
            
            # Fill author fields - adjust indices based on the SQL query
            self.author_id_var.set(author[0])  # id
            self.user_id_var.set(author[1] or "")  # userId
            self.author_name_var.set(author[2])  # author_name
            self.author_image_url_var.set(author[3] or "")  # author_image_url
            self.birth_date_var.set(author[4] or "")  # birth_date
            self.death_date_var.set(author[5] or "")  # death_date
            self.website_var.set(author[6] or "")  # website
            
            # Clear and set bio
            self.bio_text.delete("1.0", tk.END)
            if author[7]:  # bio
                self.bio_text.insert("1.0", author[7])
            
            # Preview image if available
            if author[3]:  # author_image_url
                self.preview_author_image()
            else:
                # Clear image preview
                self.author_image_preview.configure(image="")
                
            # Update author's books list
            self.update_author_books(author[0])
    
    def clear_author_fields(self):
        """Clear all author fields"""
        self.author_id_var.set("")
        self.user_id_var.set("")
        self.author_name_var.set("")
        self.author_image_url_var.set("")
        self.birth_date_var.set("")
        self.death_date_var.set("")
        self.website_var.set("")
        self.bio_text.delete("1.0", tk.END)
        
        # Clear image preview
        self.author_image_preview.configure(image="")
        
        # Clear books list
        self.books_listbox.delete(0, tk.END)
    
    def get_authors_from_db(self):
        """Get all authors from database"""
        try:
            # Use the new method from DatabaseManager
            return self.db_manager.authors.get_all()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load authors: {str(e)}")
            return []    

    def update_authors_listbox(self):
        """Update the authors listbox from database"""
        self.authors_listbox.delete(0, tk.END)
        
        authors = self.get_authors_from_db()
        
        for author in authors:
            # author_name is the third column (index 2)
            self.authors_listbox.insert(tk.END, author[2])
            
        # If there are authors, select the first one
        if self.authors_listbox.size() > 0:
            self.authors_listbox.select_set(0)
            self.authors_listbox.event_generate("<<ListboxSelect>>")
    
    def update_author_books(self, author_id):
        """Update the list of books for the selected author"""
        self.books_listbox.delete(0, tk.END)
        
        try:
            books = self.db_manager.books.get_by_author(author_id)
            
            for book in books:
                # title is the second column (index 1)
                self.books_listbox.insert(tk.END, book[1])
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load author's books: {str(e)}")
    
    def preview_author_image(self):
        """Preview the author image from URL or local file path"""
        url = self.author_image_url_var.get().strip()
        
        if not url:
            messagebox.showerror("Error", "No image URL provided")
            return
        
        try:
            # Check if we have a local version of the image first
            local_path = None
            author_id = self.author_id_var.get()
            
            if author_id:
                # Query the database for local_image_path
                query = "SELECT local_image_path FROM authors WHERE id = ?"
                results = self.db_manager.execute_query(query, (author_id,))
                
                if results and results[0][0]:
                    local_path = results[0][0]
            
            if local_path and os.path.exists(local_path):
                # Use the local image if available
                image = Image.open(local_path)
            else:
                # Fall back to downloading from URL
                response = requests.get(url)
                image = Image.open(BytesIO(response.content))
            
            # Resize to 128x128 for preview
            image = image.resize((128, 128), Image.LANCZOS)
            
            photo = ImageTk.PhotoImage(image)
            self.author_image_preview.configure(image=photo)
            self.author_image_preview.image = photo  # Keep a reference
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")
