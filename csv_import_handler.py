import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import re
from datetime import datetime

class CSVImportHandler:
    def __init__(self, parent_tab):
        self.parent_tab = parent_tab
        self.parent = parent_tab.parent  # Main app reference
        self.tab_type = self._determine_tab_type()
        self.create_import_button()
    
    def _determine_tab_type(self):
        """Determine which tab we're in"""
        if hasattr(self.parent_tab, 'authors_listbox'):
            return "Authors"
        elif hasattr(self.parent_tab, 'books_listbox'):
            return "Books"
        elif hasattr(self.parent_tab, 'genre_relations_listbox'):
            return "Genres"
        elif hasattr(self.parent_tab, 'images_listbox'):
            return "Images"
        return None
    
    def create_import_button(self):
        """Create a CSV import button in the parent's list frame"""
        # Find the appropriate list frame
        if hasattr(self.parent_tab, 'frame'):
            # Find the list frame - it should be the first child of the frame and a ttk.Frame
            for child in self.parent_tab.frame.winfo_children():
                if isinstance(child, ttk.Frame) and child.winfo_children() and isinstance(child.winfo_children()[0], ttk.Label):
                    list_frame = child
                    break
            else:
                # Fallback if list frame not found
                return
                
            # Create import button at the bottom of the list frame
            self.import_button = ttk.Button(
                list_frame, 
                text=f"Import {self.tab_type} CSV", 
                command=self.show_import_dialog
            )
            self.import_button.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
    
    def show_import_dialog(self):
        """Show the import dialog"""
        # Create a new top-level window
        self.import_dialog = tk.Toplevel(self.parent.root)
        self.import_dialog.title(f"Import {self.tab_type} CSV Data")
        self.import_dialog.geometry("400x250")
        self.import_dialog.resizable(False, False)
        self.import_dialog.transient(self.parent.root)  # Make dialog modal
        self.import_dialog.grab_set()
        
        # Center the dialog
        self.import_dialog.update_idletasks()
        width = self.import_dialog.winfo_width()
        height = self.import_dialog.winfo_height()
        x = (self.import_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.import_dialog.winfo_screenheight() // 2) - (height // 2)
        self.import_dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Create a frame for the dialog content
        content_frame = ttk.Frame(self.import_dialog, padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # File selection
        file_frame = ttk.Frame(content_frame)
        file_frame.pack(fill=tk.X, pady=5)
        
        self.file_path_var = tk.StringVar()
        ttk.Label(file_frame, text="CSV File:").pack(side=tk.LEFT)
        ttk.Entry(file_frame, textvariable=self.file_path_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Browse...", command=self.browse_csv_file).pack(side=tk.LEFT)
        
        # Hidden import type selection (we'll set this automatically)
        self.import_type_var = tk.StringVar(value=self.tab_type)
        
        # Options
        options_frame = ttk.Frame(content_frame)
        options_frame.pack(fill=tk.X, pady=5)
        
        self.skip_header_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Skip first row (header)", variable=self.skip_header_var).pack(anchor=tk.W)
        
        self.update_existing_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Update existing entries", variable=self.update_existing_var).pack(anchor=tk.W)
        
        # Preview option
        preview_frame = ttk.Frame(content_frame)
        preview_frame.pack(fill=tk.X, pady=5)
        
        self.preview_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(preview_frame, text="Preview before import", variable=self.preview_var).pack(anchor=tk.W)
        
        # Hint label
        hint_label = ttk.Label(
            content_frame, 
            text=f"Note: This will only import {self.tab_type.lower()} data",
            font=("", 9, "italic"),
            foreground="gray"
        )
        hint_label.pack(pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(content_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Cancel", command=self.import_dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Import", command=self.process_import).pack(side=tk.RIGHT)
    
    def browse_csv_file(self):
        """Browse for CSV file"""
        file_path = filedialog.askopenfilename(
            title=f"Select {self.tab_type} CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            self.file_path_var.set(file_path)
    
    def process_import(self):
        """Process the CSV import"""
        file_path = self.file_path_var.get()
        import_type = self.import_type_var.get()
        skip_header = self.skip_header_var.get()
        update_existing = self.update_existing_var.get()
        preview = self.preview_var.get()
        
        if not file_path:
            messagebox.showerror("Error", "Please select a CSV file")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as csv_file:
                csv_reader = csv.reader(csv_file)
                data = list(csv_reader)
                
                if not data:
                    messagebox.showerror("Error", "CSV file is empty")
                    return
                
                # If skip header is enabled, use the first row as header and skip it for data
                header = data[0] if data else []
                rows = data[1:] if skip_header and len(data) > 1 else data
                
                if preview:
                    self.show_preview_dialog(header, rows, import_type, update_existing)
                else:
                    self.import_data(header, rows, import_type, update_existing)
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open or read CSV file: {str(e)}")
    
    def show_preview_dialog(self, header, rows, import_type, update_existing):
        """Show preview of CSV data before import"""
        preview_dialog = tk.Toplevel(self.parent.root)
        preview_dialog.title(f"CSV Import Preview - {import_type}")
        preview_dialog.geometry("800x500")
        preview_dialog.transient(self.import_dialog)
        preview_dialog.grab_set()
        
        # Center the dialog
        preview_dialog.update_idletasks()
        width = preview_dialog.winfo_width()
        height = preview_dialog.winfo_height()
        x = (preview_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (preview_dialog.winfo_screenheight() // 2) - (height // 2)
        preview_dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Frame for the dialog content
        content_frame = ttk.Frame(preview_dialog, padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Preview label
        ttk.Label(content_frame, text=f"Preview of {len(rows)} rows for import into {import_type}").pack(pady=5)
        
        # Create treeview for data preview
        preview_frame = ttk.Frame(content_frame)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create scrollbar
        scrollbar = ttk.Scrollbar(preview_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create treeview
        tree = ttk.Treeview(
            preview_frame, 
            columns=list(range(len(header))), 
            show="headings",
            yscrollcommand=scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Configure scrollbars
        scrollbar.config(command=tree.yview)
        h_scrollbar.config(command=tree.xview)
        
        # Set column headings
        for i, col in enumerate(header):
            tree.heading(i, text=col)
            tree.column(i, width=100, stretch=tk.YES)
        
        # Add data rows
        for i, row in enumerate(rows[:100]):  # Limit to 100 rows in preview
            # Ensure row has enough columns by padding with empty strings
            padded_row = row + [''] * (len(header) - len(row))
            tree.insert('', tk.END, values=padded_row[:len(header)])
        
        # Show message if there are more rows
        if len(rows) > 100:
            ttk.Label(content_frame, text=f"(Showing first 100 of {len(rows)} rows)").pack(pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(content_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Cancel", command=preview_dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(
            btn_frame, 
            text="Import Data", 
            command=lambda: [
                preview_dialog.destroy(), 
                self.import_data(header, rows, import_type, update_existing)
            ]
        ).pack(side=tk.RIGHT)
    
    def import_data(self, header, rows, import_type, update_existing):
        """Import the CSV data based on the selected import type"""
        try:
            if import_type == "Authors":
                self.import_authors(header, rows, update_existing)
            elif import_type == "Books":
                self.import_books(header, rows, update_existing)
            elif import_type == "Genres":
                self.import_genres(header, rows, update_existing)
            elif import_type == "Images":
                # Add image import function if needed
                messagebox.showerror("Error", "Image import not implemented yet")
                return
            else:
                messagebox.showerror("Error", f"Unknown import type: {import_type}")
                return
            
            # Close the import dialog
            if self.import_dialog.winfo_exists():
                self.import_dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import data: {str(e)}")
    
    def import_authors(self, header, rows, update_existing):
        """Import author data from CSV"""
        # Define column mappings (header to author field)
        mappings = {
            "author_name": ["author_name", "author", "name", "author name", "full name"],
            "author_image_url": ["author_image_url", "image_url", "image", "photo", "picture", "avatar"],
            "birth_date": ["birth_date", "birthdate", "birth", "born", "date of birth", "dob"],
            "death_date": ["death_date", "deathdate", "death", "died", "date of death", "dod"],
            "website": ["website", "web", "site", "url", "webpage", "web page"],
            "bio": ["bio", "biography", "about", "description", "profile"]
        }
        
        # Find column indices
        column_indices = self._find_column_indices(header, mappings)
        
        # Process rows
        authors_added = 0
        authors_updated = 0
        authors_skipped = 0
        
        for row in rows:
            # Skip empty rows
            if not any(cell.strip() for cell in row if cell):
                continue
            
            # Get author data from row
            author_name = self._get_value_from_row(row, column_indices, "author_name")
            
            if not author_name:
                authors_skipped += 1
                continue
            
            author_data = {
                "author_name": author_name,
                "author_image_url": self._get_value_from_row(row, column_indices, "author_image_url"),
                "birth_date": self._get_value_from_row(row, column_indices, "birth_date"),
                "death_date": self._get_value_from_row(row, column_indices, "death_date"),
                "website": self._get_value_from_row(row, column_indices, "website"),
                "bio": self._get_value_from_row(row, column_indices, "bio")
            }
            
            # Check if author already exists
            author_index = None
            for i, author in enumerate(self.parent.authors):
                if author["author_name"] == author_name:
                    author_index = i
                    break
            
            if author_index is not None:
                if update_existing:
                    # Update existing author
                    self.parent.authors[author_index] = author_data
                    authors_updated += 1
                else:
                    authors_skipped += 1
            else:
                # Add new author
                self.parent.authors.append(author_data)
                authors_added += 1
        
        # Update UI
        self.parent.authors_tab.update_authors_listbox()
        self.parent.books_tab.update_book_author_dropdown()
        self.parent.images_tab.update_image_item_dropdown()
        self.parent.update_export_status()
        
        # Show summary
        messagebox.showinfo(
            "Import Complete",
            f"Authors import summary:\n"
            f"- Added: {authors_added}\n"
            f"- Updated: {authors_updated}\n"
            f"- Skipped: {authors_skipped}"
        )
    
    def import_books(self, header, rows, update_existing):
        """Import book data from CSV"""
        # Define column mappings (header to book field)
        mappings = {
            "title": ["title", "book title", "book name", "name"],
            "author": ["author", "author name", "writer"],
            "description": ["description", "desc", "summary", "overview", "book description"],
            "internal_details": ["internal_details", "internal", "notes", "private notes", "internal notes"],
            "page_count": ["page_count", "pages", "length", "page length", "number of pages"],
            "formats": ["formats", "format", "book format", "available formats", "format type"],
            "publish_date": ["publish_date", "publication date", "published", "release date", "date published"],
            "awards": ["awards", "award", "prize", "prizes", "recognition"],
            "series": ["series", "series name", "book series", "collection"],
            "setting": ["setting", "location", "place", "world", "environment"],
            "characters": ["characters", "character", "main characters", "protagonists", "people"],
            "language": ["language", "lang", "written in", "original language"],
            "referral_links": ["referral_links", "buy links", "store links", "purchase links", "affiliate links"]
        }
        
        # Find column indices
        column_indices = self._find_column_indices(header, mappings)
        
        # Process rows
        books_added = 0
        books_updated = 0
        books_skipped = 0
        
        for row in rows:
            # Skip empty rows
            if not any(cell.strip() for cell in row if cell):
                continue
            
            # Get book data from row
            title = self._get_value_from_row(row, column_indices, "title")
            author = self._get_value_from_row(row, column_indices, "author")
            
            if not title or not author:
                books_skipped += 1
                continue
            
            # Process formats (comma separated values)
            formats_str = self._get_value_from_row(row, column_indices, "formats") or ""
            formats = []
            
            if formats_str:
                format_values = [f.strip().lower() for f in formats_str.split(",")]
                valid_formats = ["digital", "softback", "hardback", "audiobook"]
                for fmt in format_values:
                    if fmt in valid_formats:
                        formats.append(fmt)
            
            if not formats:  # Default to digital if no formats provided
                formats = ["digital"]
            
            # Process page count
            page_count_str = self._get_value_from_row(row, column_indices, "page_count") or "0"
            try:
                page_count = int(page_count_str)
                if page_count <= 0:
                    page_count = 1
            except ValueError:
                page_count = 1
            
            # Process characters (comma separated)
            characters_str = self._get_value_from_row(row, column_indices, "characters") or ""
            characters = [c.strip() for c in characters_str.split(",") if c.strip()]
            
            # Process publish date
            publish_date = self._get_value_from_row(row, column_indices, "publish_date") or ""
            # Try to standardize the date format to YYYY-MM-DD
            if publish_date:
                try:
                    # Try common date formats
                    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%m-%d-%Y", "%d-%m-%Y"]:
                        try:
                            parsed_date = datetime.strptime(publish_date, fmt)
                            publish_date = parsed_date.strftime("%Y-%m-%d")
                            break
                        except ValueError:
                            continue
                except Exception:
                    # If all parsing attempts fail, leave as is
                    pass
            
            # If format still doesn't match, default to current date
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", publish_date):
                publish_date = datetime.now().strftime("%Y-%m-%d")
            
            book_data = {
                "title": title,
                "author": author,
                "description": self._get_value_from_row(row, column_indices, "description") or "No description provided.",
                "internal_details": self._get_value_from_row(row, column_indices, "internal_details") or "",
                "page_count": page_count,
                "formats": formats,
                "publish_date": publish_date,
                "awards": self._get_value_from_row(row, column_indices, "awards") or "",
                "series": self._get_value_from_row(row, column_indices, "series") or "",
                "setting": self._get_value_from_row(row, column_indices, "setting") or "",
                "characters": characters,
                "language": self._get_value_from_row(row, column_indices, "language") or "English",
                "referral_links": self._get_value_from_row(row, column_indices, "referral_links") or ""
            }
            
            # Check if book already exists
            book_index = None
            for i, book in enumerate(self.parent.books):
                if book["title"] == title:
                    book_index = i
                    break
            
            if book_index is not None:
                if update_existing:
                    # Update existing book
                    self.parent.books[book_index] = book_data
                    books_updated += 1
                else:
                    books_skipped += 1
            else:
                # Add new book
                self.parent.books.append(book_data)
                books_added += 1
        
        # Update UI
        self.parent.books_tab.update_books_listbox()
        self.parent.genres_tab.update_genre_book_dropdown()
        self.parent.images_tab.update_image_item_dropdown()
        self.parent.update_export_status()
        
        # Show summary
        messagebox.showinfo(
            "Import Complete",
            f"Books import summary:\n"
            f"- Added: {books_added}\n"
            f"- Updated: {books_updated}\n"
            f"- Skipped: {books_skipped}"
        )
    
    def import_genres(self, header, rows, update_existing):
        """Import genre relations from CSV"""
        # Define column mappings (header to genre fields)
        mappings = {
            "book": ["book", "title", "book title", "book name"],
            "genres": ["genres", "genre", "categories", "tags", "book genres"]
        }
        
        # Find column indices
        column_indices = self._find_column_indices(header, mappings)
        
        # Valid genres list
        valid_genres = [
            "Fiction", "Non-Fiction", "Mystery", "Thriller", "Romance", "Science Fiction", 
            "Fantasy", "Horror", "Biography", "History", "Self-Help", "Philosophy",
            "Politics", "Science", "Technology", "Art", "Travel", "Cooking", 
            "Health", "Religion", "Children's", "Young Adult", "Poetry", "Comics",
            "Drama", "Comedy", "Adventure", "Dystopian", "Historical Fiction", "Memoir"
        ]
        
        # Process rows
        relations_added = 0
        relations_updated = 0
        relations_skipped = 0
        
        for row in rows:
            # Skip empty rows
            if not any(cell.strip() for cell in row if cell):
                continue
            
            # Get genre relation data from row
            book = self._get_value_from_row(row, column_indices, "book")
            genres_str = self._get_value_from_row(row, column_indices, "genres")
            
            if not book or not genres_str:
                relations_skipped += 1
                continue
            
            # Verify book exists
            book_exists = False
            for b in self.parent.books:
                if b["title"] == book:
                    book_exists = True
                    break
            
            if not book_exists:
                relations_skipped += 1
                continue
            
            # Process genres (comma separated values)
            genre_list = [g.strip() for g in genres_str.split(",") if g.strip()]
            
            # Filter to only valid genres
            valid_genre_list = [g for g in genre_list if g in valid_genres]
            
            # Ensure we have at least 5 genres (requirement from your code)
            if len(valid_genre_list) < 5:
                # If we have less than 5, add default genres to reach 5
                remaining = 5 - len(valid_genre_list)
                for genre in valid_genres:
                    if genre not in valid_genre_list:
                        valid_genre_list.append(genre)
                        remaining -= 1
                        if remaining == 0:
                            break
            
            # Create genre relation
            relation = {
                "book": book,
                "genres": valid_genre_list
            }
            
            # Check if relation already exists
            relation_index = None
            for i, r in enumerate(self.parent.genre_relations):
                if r["book"] == book:
                    relation_index = i
                    break
            
            if relation_index is not None:
                if update_existing:
                    # Update existing relation
                    self.parent.genre_relations[relation_index] = relation
                    relations_updated += 1
                else:
                    relations_skipped += 1
            else:
                # Add new relation
                self.parent.genre_relations.append(relation)
                relations_added += 1
        
        # Update UI
        self.parent.genres_tab.update_genre_relations_listbox()
        self.parent.update_export_status()
        
        # Show summary
        messagebox.showinfo(
            "Import Complete",
            f"Genre relations import summary:\n"
            f"- Added: {relations_added}\n"
            f"- Updated: {relations_updated}\n"
            f"- Skipped: {relations_skipped}"
        )
    
    def _find_column_indices(self, header, mappings):
        """Find column indices based on header mappings"""
        column_indices = {}
        
        # Convert header to lowercase for case-insensitive matching
        header_lower = [h.lower() if h else "" for h in header]
        
        for field, possible_names in mappings.items():
            column_indices[field] = None
            for name in possible_names:
                if name.lower() in header_lower:
                    column_indices[field] = header_lower.index(name.lower())
                    break
        
        return column_indices
    
    def _get_value_from_row(self, row, column_indices, field):
        """Get value from row based on field mapping"""
        index = column_indices.get(field)
        if index is not None and index < len(row):
            return row[index]
        return ""
