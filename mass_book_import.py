# books_mass_import.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import csv
import json
import os
from datetime import datetime
import re
import app_logger as logger

class BooksMassImport:
    def __init__(self, parent_tab):
        self.parent_tab = parent_tab
        self.parent = parent_tab.parent  # Main app reference
        self.db_manager = self.parent.db_manager if hasattr(self.parent, 'db_manager') else None
        
        # Create the import button
        self.create_import_button()
        
    def create_import_button(self):
        """Create a mass import button in the books tab"""
        if hasattr(self.parent_tab, 'frame'):
            # Find an appropriate location for the button
            for child in self.parent_tab.frame.winfo_children():
                if isinstance(child, ttk.Frame) and hasattr(child, 'winfo_children'):
                    for subchild in child.winfo_children():
                        if isinstance(subchild, ttk.Frame) and hasattr(subchild, 'winfo_children'):
                            for button_frame in subchild.winfo_children():
                                if isinstance(button_frame, ttk.Frame):
                                    # Found the button frame, add our mass import button
                                    self.import_button = ttk.Button(
                                        button_frame, 
                                        text="Mass Import", 
                                        command=self.show_import_dialog
                                    )
                                    self.import_button.pack(side=tk.LEFT, padx=5)
                                    return
            
            # If we couldn't find the button frame, create a new one at the bottom of the books list frame
            btn_frame = ttk.Frame(self.parent_tab.frame)
            btn_frame.pack(fill=tk.X, pady=5, side=tk.BOTTOM)
            
            self.import_button = ttk.Button(
                btn_frame, 
                text="Mass Import Books", 
                command=self.show_import_dialog
            )
            self.import_button.pack(fill=tk.X, padx=5)
    
    def show_import_dialog(self):
        """Show the mass import dialog"""
        # Create a new top-level window
        self.import_dialog = tk.Toplevel(self.parent.root)
        self.import_dialog.title("Mass Import Books")
        self.import_dialog.geometry("600x500")
        self.import_dialog.resizable(True, True)
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
        
        # File selection - support multiple file formats
        file_frame = ttk.Frame(content_frame)
        file_frame.pack(fill=tk.X, pady=5)
        
        self.file_path_var = tk.StringVar()
        ttk.Label(file_frame, text="Import File:").pack(side=tk.LEFT)
        ttk.Entry(file_frame, textvariable=self.file_path_var, width=50).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(file_frame, text="Browse...", command=self.browse_import_file).pack(side=tk.LEFT)
        
        # File format selection
        format_frame = ttk.LabelFrame(content_frame, text="File Format")
        format_frame.pack(fill=tk.X, pady=5)
        
        self.file_format_var = tk.StringVar(value="csv")
        ttk.Radiobutton(format_frame, text="CSV", variable=self.file_format_var, value="csv").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(format_frame, text="Excel", variable=self.file_format_var, value="excel").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(format_frame, text="JSON", variable=self.file_format_var, value="json").pack(side=tk.LEFT, padx=10)
        
        # Options
        options_frame = ttk.LabelFrame(content_frame, text="Import Options")
        options_frame.pack(fill=tk.X, pady=5)
        
        self.skip_header_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Skip first row (header)", variable=self.skip_header_var).pack(anchor=tk.W)
        
        self.update_existing_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Update existing entries", variable=self.update_existing_var).pack(anchor=tk.W)
        
        self.validate_data_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Validate data before import", variable=self.validate_data_var).pack(anchor=tk.W)
        
        self.import_taxonomies_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Import taxonomies if included", variable=self.import_taxonomies_var).pack(anchor=tk.W)
        
        # Template download
        template_frame = ttk.Frame(content_frame)
        template_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(template_frame, text="Need a template?").pack(side=tk.LEFT)
        ttk.Button(template_frame, text="Download CSV Template", command=lambda: self.download_template("csv")).pack(side=tk.LEFT, padx=5)
        ttk.Button(template_frame, text="Download Excel Template", command=lambda: self.download_template("excel")).pack(side=tk.LEFT, padx=5)
        
        # Status and progress
        status_frame = ttk.Frame(content_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.status_var = tk.StringVar(value="Ready to import.")
        ttk.Label(status_frame, textvariable=self.status_var).pack(anchor=tk.W)
        
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Field mapping display
        mapping_frame = ttk.LabelFrame(content_frame, text="Field Mapping")
        mapping_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create a canvas with scrollbar for the mapping fields
        canvas = tk.Canvas(mapping_frame)
        scrollbar = ttk.Scrollbar(mapping_frame, orient="vertical", command=canvas.yview)
        self.mapping_inner_frame = ttk.Frame(canvas)
        
        self.mapping_inner_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.mapping_inner_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add initial mapping info
        ttk.Label(self.mapping_inner_frame, text="Import a file to see field mapping").grid(row=0, column=0, padx=5, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(content_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Cancel", command=self.import_dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Preview", command=self.preview_import).pack(side=tk.RIGHT, padx=5)
        self.import_btn = ttk.Button(btn_frame, text="Start Import", command=self.process_import, state=tk.DISABLED)
        self.import_btn.pack(side=tk.RIGHT, padx=5)
    
    def browse_import_file(self):
        """Browse for import file"""
        file_format = self.file_format_var.get()
        filetypes = []
        
        if file_format == "csv":
            filetypes = [("CSV files", "*.csv"), ("All files", "*.*")]
        elif file_format == "excel":
            filetypes = [("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        elif file_format == "json":
            filetypes = [("JSON files", "*.json"), ("All files", "*.*")]
        
        file_path = filedialog.askopenfilename(
            title=f"Select {file_format.upper()} File for Import",
            filetypes=filetypes
        )
        
        if file_path:
            self.file_path_var.set(file_path)
            # Try to analyze the file structure
            self.analyze_file_structure(file_path)
    
    def analyze_file_structure(self, file_path):
        """Analyze the structure of the import file"""
        try:
            file_format = self.file_format_var.get()
            self.status_var.set(f"Analyzing {file_format.upper()} file...")
            self.import_btn.config(state=tk.DISABLED)
            
            # Clear existing mapping widgets
            for widget in self.mapping_inner_frame.winfo_children():
                widget.destroy()
            
            # Load file based on format
            if file_format == "csv":
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    headers = next(reader)
                    first_row = next(reader, None)
            elif file_format == "excel":
                df = pd.read_excel(file_path)
                headers = df.columns.tolist()
                first_row = df.iloc[0].tolist() if not df.empty else None
            elif file_format == "json":
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list) and data:
                        headers = list(data[0].keys())
                        first_row = list(data[0].values())
                    else:
                        headers = []
                        first_row = None
            
            # Book field mapping options
            book_fields = [
                "title", "author", "description", "internal_details", "page_count", 
                "formats", "publish_date", "awards", "series", "setting", 
                "characters", "language", "referral_links", "isbn", "asin"
            ]
            
            # Display mapping header
            ttk.Label(self.mapping_inner_frame, text="File Column").grid(row=0, column=0, padx=5, pady=5)
            ttk.Label(self.mapping_inner_frame, text="Maps to Book Field").grid(row=0, column=1, padx=5, pady=5)
            ttk.Label(self.mapping_inner_frame, text="Sample Value").grid(row=0, column=2, padx=5, pady=5)
            
            ttk.Separator(self.mapping_inner_frame, orient='horizontal').grid(row=1, column=0, columnspan=3, sticky='ew', pady=5)
            
            # Create mapping comboboxes for each header
            self.mapping_vars = {}
            for i, header in enumerate(headers):
                ttk.Label(self.mapping_inner_frame, text=header).grid(row=i+2, column=0, padx=5, pady=2, sticky=tk.W)
                
                mapping_var = tk.StringVar()
                mapping_combo = ttk.Combobox(self.mapping_inner_frame, textvariable=mapping_var, values=book_fields, width=30)
                mapping_combo.grid(row=i+2, column=1, padx=5, pady=2)
                
                # Try to auto-map common field names
                lower_header = header.lower().replace(" ", "_")
                if lower_header in book_fields:
                    mapping_var.set(lower_header)
                elif lower_header == "pages" or lower_header == "page_number":
                    mapping_var.set("page_count")
                elif lower_header == "publication_date" or lower_header == "published":
                    mapping_var.set("publish_date")
                elif lower_header == "book_title" or lower_header == "name":
                    mapping_var.set("title")
                elif lower_header == "author_name" or lower_header == "writer":
                    mapping_var.set("author")
                
                # Display sample value if available
                if first_row and i < len(first_row):
                    sample_value = str(first_row[i])
                    if len(sample_value) > 30:
                        sample_value = sample_value[:27] + "..."
                    ttk.Label(self.mapping_inner_frame, text=sample_value).grid(row=i+2, column=2, padx=5, pady=2, sticky=tk.W)
                
                self.mapping_vars[header] = mapping_var
            
            # Add taxonomies mapping section if enabled
            if self.import_taxonomies_var.get():
                taxonomy_row = len(headers) + 3
                ttk.Separator(self.mapping_inner_frame, orient='horizontal').grid(
                    row=taxonomy_row, column=0, columnspan=3, sticky='ew', pady=5
                )
                
                ttk.Label(self.mapping_inner_frame, text="Taxonomy Mapping", font=('', 10, 'bold')).grid(
                    row=taxonomy_row+1, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W
                )
                
                ttk.Label(self.mapping_inner_frame, text="Taxonomies not yet supported in mass import.").grid(
                    row=taxonomy_row+2, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W
                )
                
                ttk.Label(self.mapping_inner_frame, text="You will need to add taxonomies manually after import.").grid(
                    row=taxonomy_row+3, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W
                )
            
            self.status_var.set("File analyzed successfully. Review mapping and click Preview.")
            self.import_btn.config(state=tk.NORMAL)
            
        except Exception as e:
            logger.log_error(f"Error analyzing file: {str(e)}")
            messagebox.showerror("Error", f"Failed to analyze file: {str(e)}")
            self.status_var.set(f"Error: {str(e)}")
    
    def preview_import(self):
        """Preview the data to be imported"""
        file_path = self.file_path_var.get()
        
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Error", "Please select a valid file")
            return
        
        try:
            # Load and transform the data
            data = self.load_and_transform_data(file_path)
            
            if not data:
                messagebox.showerror("Error", "No valid data found in file")
                return
            
            # Create preview dialog
            preview_dialog = tk.Toplevel(self.import_dialog)
            preview_dialog.title(f"Import Preview - {len(data)} Books")
            preview_dialog.geometry("800x600")
            preview_dialog.transient(self.import_dialog)
            preview_dialog.grab_set()
            
            # Center the dialog
            preview_dialog.update_idletasks()
            preview_dialog.geometry("+%d+%d" % (
                self.import_dialog.winfo_rootx() + 50,
                self.import_dialog.winfo_rooty() + 50
            ))
            
            # Create treeview for data preview
            preview_frame = ttk.Frame(preview_dialog, padding=10)
            preview_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(preview_frame, text=f"Preview of {len(data)} books to import:").pack(anchor=tk.W, pady=5)
            
            # Create treeview with scrollbars
            tree_frame = ttk.Frame(preview_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            
            # Create vertical scrollbar
            v_scrollbar = ttk.Scrollbar(tree_frame)
            v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Create horizontal scrollbar
            h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
            h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
            
            # Define columns for treeview
            columns = ("title", "author", "page_count", "publish_date", "language", "formats")
            column_headings = {
                "title": "Title", 
                "author": "Author", 
                "page_count": "Pages", 
                "publish_date": "Publish Date",
                "language": "Language",
                "formats": "Formats"
            }
            
            tree = ttk.Treeview(
                tree_frame, 
                columns=columns,
                show="headings",
                yscrollcommand=v_scrollbar.set,
                xscrollcommand=h_scrollbar.set
            )
            
            # Configure scrollbars
            v_scrollbar.config(command=tree.yview)
            h_scrollbar.config(command=tree.xview)
            
            # Configure columns
            for col in columns:
                tree.heading(col, text=column_headings.get(col, col.capitalize()))
                tree.column(col, width=100, minwidth=50)
            
            tree.column("title", width=200)
            tree.column("author", width=150)
            
            # Add data rows
            for book in data[:100]:  # Limit preview to 100 rows
                row_values = []
                for col in columns:
                    val = book.get(col, "")
                    if isinstance(val, list):
                        val = ", ".join(val)
                    row_values.append(str(val))
                tree.insert("", tk.END, values=row_values)
            
            tree.pack(fill=tk.BOTH, expand=True)
            
            # Show remaining count if more than 100 books
            if len(data) > 100:
                ttk.Label(preview_frame, text=f"(Showing first 100 of {len(data)} books)").pack(anchor=tk.W, pady=5)
            
            # Validation results
            if self.validate_data_var.get():
                validation_issues = self.validate_import_data(data)
                if validation_issues:
                    issues_frame = ttk.LabelFrame(preview_frame, text="Validation Issues")
                    issues_frame.pack(fill=tk.X, pady=5)
                    
                    issues_text = tk.Text(issues_frame, height=5, wrap=tk.WORD)
                    issues_text.pack(fill=tk.X, pady=5)
                    
                    for issue in validation_issues[:10]:
                        issues_text.insert(tk.END, f"• {issue}\n")
                    
                    if len(validation_issues) > 10:
                        issues_text.insert(tk.END, f"(Plus {len(validation_issues) - 10} more issues)\n")
                    
                    issues_text.config(state=tk.DISABLED)
            
            # Buttons
            btn_frame = ttk.Frame(preview_frame)
            btn_frame.pack(fill=tk.X, pady=10)
            
            ttk.Button(btn_frame, text="Cancel", command=preview_dialog.destroy).pack(side=tk.RIGHT, padx=5)
            ttk.Button(
                btn_frame, 
                text="Import All Books", 
                command=lambda: [preview_dialog.destroy(), self.process_import()]
            ).pack(side=tk.RIGHT, padx=5)
            
        except Exception as e:
            logger.log_error(f"Error in preview: {str(e)}")
            messagebox.showerror("Error", f"Failed to generate preview: {str(e)}")
    
    def load_and_transform_data(self, file_path):
        """Load data from file and transform according to mapping"""
        file_format = self.file_format_var.get()
        skip_header = self.skip_header_var.get()
        
        raw_data = []
        
        try:
            # Load raw data based on file format
            if file_format == "csv":
                df = pd.read_csv(file_path, header=0 if skip_header else None)
                raw_data = df.to_dict('records')
            elif file_format == "excel":
                df = pd.read_excel(file_path, header=0 if skip_header else None)
                raw_data = df.to_dict('records')
            elif file_format == "json":
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                
                # If skip_header is True and it's a list, skip the first row
                if skip_header and isinstance(raw_data, list) and len(raw_data) > 0:
                    raw_data = raw_data[1:]
            
            # Transform data according to mapping
            transformed_data = []
            for row in raw_data:
                book_data = {}
                
                for file_field, mapping_var in self.mapping_vars.items():
                    book_field = mapping_var.get()
                    
                    if book_field and file_field in row:
                        value = row[file_field]
                        
                        # Handle special transformations
                        if book_field == "formats":
                            if isinstance(value, str):
                                value = [v.strip().lower() for v in value.split(',')]
                            elif isinstance(value, (int, float, bool)):
                                value = [str(value).lower()]
                            if not value:
                                value = ["digital"]  # Default to digital if empty
                        
                        elif book_field == "page_count":
                            try:
                                value = int(value)
                                if value <= 0:
                                    value = 1
                            except (ValueError, TypeError):
                                value = 1
                        
                        elif book_field == "characters":
                            if isinstance(value, str):
                                value = [v.strip() for v in value.split(',') if v.strip()]
                        
                        elif book_field == "publish_date":
                            # If provided date is not in YYYY-MM-DD format, try to convert it
                            if value and isinstance(value, str) and not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
                                try:
                                    # Try common date formats
                                    for fmt in ["%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%m-%d-%Y", "%d-%m-%Y"]:
                                        try:
                                            parsed_date = datetime.strptime(value, fmt)
                                            value = parsed_date.strftime("%Y-%m-%d")
                                            break
                                        except ValueError:
                                            continue
                                except Exception:
                                    # If all parsing attempts fail, use current date
                                    value = datetime.now().strftime("%Y-%m-%d")
                            
                            # If still not in the right format, default to current date
                            if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(value)):
                                value = datetime.now().strftime("%Y-%m-%d")
                        
                        book_data[book_field] = value
                
                # Add required fields if missing
                if "title" not in book_data or not book_data["title"]:
                    continue  # Skip books without title
                
                if "author" not in book_data or not book_data["author"]:
                    continue  # Skip books without author
                
                if "description" not in book_data or not book_data["description"]:
                    book_data["description"] = "No description provided."
                
                if "language" not in book_data or not book_data["language"]:
                    book_data["language"] = "English"
                
                if "formats" not in book_data or not book_data["formats"]:
                    book_data["formats"] = ["digital"]
                
                if "page_count" not in book_data:
                    book_data["page_count"] = 1
                
                if "publish_date" not in book_data:
                    book_data["publish_date"] = datetime.now().strftime("%Y-%m-%d")
                
                if "characters" not in book_data:
                    book_data["characters"] = []
                
                transformed_data.append(book_data)
            
            return transformed_data
            
        except Exception as e:
            logger.log_error(f"Error loading and transforming data: {str(e)}")
            raise
    
    def validate_import_data(self, data):
        """Validate the data to be imported"""
        validation_issues = []
        
        for i, book in enumerate(data):
            book_num = i + 1
            
            # Check for missing required fields
            if not book.get("title"):
                validation_issues.append(f"Book #{book_num}: Missing title")
            
            if not book.get("author"):
                validation_issues.append(f"Book #{book_num}: Missing author")
            
            # Validate date format
            publish_date = book.get("publish_date")
            if publish_date and not re.match(r"^\d{4}-\d{2}-\d{2}$", str(publish_date)):
                validation_issues.append(f"Book #{book_num}: Invalid publish date format for '{book.get('title')}' - expected YYYY-MM-DD")
            
            # Validate page count
            page_count = book.get("page_count")
            if page_count is not None:
                try:
                    page_count = int(page_count)
                    if page_count <= 0:
                        validation_issues.append(f"Book #{book_num}: Invalid page count for '{book.get('title')}' - must be positive")
                except (ValueError, TypeError):
                    validation_issues.append(f"Book #{book_num}: Invalid page count for '{book.get('title')}' - must be a number")
            
            # Check if book already exists in database
            if hasattr(self.parent, 'db_manager') and self.parent.db_manager:
                existing_books = self.parent.db_manager.execute_query(
                    "SELECT id FROM books WHERE title = ? AND author = ?", 
                    (book.get("title"), book.get("author"))
                )
                
                if existing_books and not self.update_existing_var.get():
                    validation_issues.append(f"Book #{book_num}: '{book.get('title')}' by {book.get('author')} already exists and update option is disabled")
        
        return validation_issues
    
    def process_import(self):
        """Process the actual import of books"""
        file_path = self.file_path_var.get()
        
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Error", "Please select a valid file")
            return
        
        try:
            # Load and transform the data
            data = self.load_and_transform_data(file_path)
            
            if not data:
                messagebox.showerror("Error", "No valid data found in file")
                return
            
            # Initialize counters
            total_books = len(data)
            books_added = 0
            books_updated = 0
            books_skipped = 0
            current_book = 0
            
            # Begin import process
            self.status_var.set(f"Importing {total_books} books...")
            self.progress_var.set(0)
            self.import_dialog.update_idletasks()
            
            for book in data:
                current_book += 1
                self.progress_var.set((current_book / total_books) * 100)
                self.status_var.set(f"Importing book {current_book} of {total_books}: {book.get('title')}")
                self.import_dialog.update_idletasks()
                
                # Check if book already exists
                title = book.get("title", "").strip()
                author = book.get("author", "").strip()
                
                if not title or not author:
                    books_skipped += 1
                    continue
                
                # Try to find author ID in database
                author_id = None
                if hasattr(self.parent, 'db_manager') and self.parent.db_manager:
                    try:
                        author_results = self.parent.db_manager.execute_query(
                            "SELECT id FROM authors WHERE author_name = ?", 
                            (author,)
                        )
                        
                        if author_results:
                            author_id = author_results[0][0]
                        else:
                            # Author doesn't exist, create it
                            author_data = {
                                "author_name": author,
                                "bio": f"Author of {title}"
                            }
                            
                            author_id = self.parent.db_manager.authors.add(author_data)
                            logger.log_debug(f"Created new author: {author} with ID {author_id}")
                    except Exception as e:
                        logger.log_error(f"Error checking author: {str(e)}")
                
                # Process formats
                formats = book.get("formats", ["digital"])
                if isinstance(formats, str):
                    formats = [f.strip().lower() for f in formats.split(',') if f.strip()]
                
                # Process characters
                characters = book.get("characters", [])
                if isinstance(characters, str):
                    characters = [c.strip() for c in characters.split(',') if c.strip()]
                
                # Prepare book data
                book_data = {
                    "title": title,
                    "author": author,
                    "author_id": author_id,
                    "description": book.get("description", "No description provided."),
                    "internal_details": book.get("internal_details", ""),
                    "page_count": book.get("page_count", 1),
                    "formats": formats,
                    "publish_date": book.get("publish_date", datetime.now().strftime("%Y-%m-%d")),
                    "awards": book.get("awards", ""),
                    "series": book.get("series", ""),
                    "setting": book.get("setting", ""),
                    "characters": characters,
                    "language": book.get("language", "English"),
                    "referral_links": book.get("referral_links", ""),
                    "isbn": book.get("isbn", ""),
                    "asin": book.get("asin", "")
                }
                
                # Check if book already exists
                book_index = None
                book_id = None
                
                if hasattr(self.parent, 'db_manager') and self.parent.db_manager:
                    try:
                        existing_books = self.parent.db_manager.execute_query(
                            "SELECT id FROM books WHERE title = ? AND (author = ? OR authorId = ?)", 
                            (title, author, author_id)
                        )
                        
                        if existing_books:
                            book_id = existing_books[0][0]
                            
                            if self.update_existing_var.get():
                                # Update existing book in database
                                self.parent.db_manager.books.update(book_id, book_data)
                                books_updated += 1
                                logger.log_debug(f"Updated book: {title} with ID {book_id}")
                            else:
                                # Skip this book
                                books_skipped += 1
                                continue
                        else:
                            # Add new book to database
                            book_id = self.parent.db_manager.books.add(book_data)
                            books_added += 1
                            logger.log_debug(f"Added book: {title} with ID {book_id}")
                    except Exception as e:
                        logger.log_error(f"Error adding/updating book in database: {str(e)}")
                        books_skipped += 1
                        continue
                else:
                    # Check in-memory data if no database
                    for i, existing_book in enumerate(self.parent.books):
                        if isinstance(existing_book, dict) and existing_book.get("title") == title:
                            book_index = i
                            break
                    
                    if book_index is not None:
                        if self.update_existing_var.get():
                            # Update existing book in memory
                            self.parent.books[book_index] = book_data
                            books_updated += 1
                        else:
                            # Skip this book
                            books_skipped += 1
                            continue
                    else:
                        # Add new book to memory
                        self.parent.books.append(book_data)
                        books_added += 1
            
            # Update UI after import
            self.parent.books_tab.update_books_listbox()
            if hasattr(self.parent, 'genres_tab') and hasattr(self.parent.genres_tab, 'update_genre_book_dropdown'):
                self.parent.genres_tab.update_genre_book_dropdown()
            
            if hasattr(self.parent, 'images_tab') and hasattr(self.parent.images_tab, 'update_image_item_dropdown'):
                self.parent.images_tab.update_image_item_dropdown()
            
            if hasattr(self.parent, 'update_export_status'):
                self.parent.update_export_status()
            
            # Force update author dropdown
            if hasattr(self.parent_tab, 'force_author_dropdown_update'):
                self.parent_tab.force_author_dropdown_update()
            
            # Show summary
            summary = (
                f"Books import summary:\n"
                f"- Added: {books_added}\n"
                f"- Updated: {books_updated}\n"
                f"- Skipped: {books_skipped}\n"
                f"- Total: {total_books}"
            )
            
            self.status_var.set("Import completed!")
            messagebox.showinfo("Import Complete", summary)
            
            # Log import stats
            logger.log_debug(f"Mass import completed: {summary}")
            
        except Exception as e:
            logger.log_error(f"Error importing books: {str(e)}")
            messagebox.showerror("Error", f"Failed to import books: {str(e)}")
            self.status_var.set(f"Error: {str(e)}")
    
    def download_template(self, template_type):
        """Download a template file for importing books"""
        if template_type not in ["csv", "excel"]:
            messagebox.showerror("Error", "Unsupported template type")
            return
        
        # Define the template data
        template_data = {
            "title": ["Example Book Title 1", "Example Book Title 2"],
            "author": ["Author Name 1", "Author Name 2"],
            "description": ["Book description goes here.", "Another example description."],
            "internal_details": ["Internal notes for publisher", "More internal details"],
            "page_count": [324, 512],
            "formats": ["digital,hardback", "digital,softback,audiobook"],
            "publish_date": ["2023-05-15", "2022-11-30"],
            "awards": ["Literary Award, Best Fiction 2023", ""],
            "series": ["Fantasy Series Name", ""],
            "setting": ["Medieval Fantasy World", "Modern Day London"],
            "characters": ["Character 1, Character 2, Character 3", "Main Character, Supporting Character"],
            "language": ["English", "Spanish"],
            "referral_links": ["amazon.com/book1", "amazon.com/book2,barnesandnoble.com/book2"],
            "isbn": ["978-3-16-148410-0", "978-1-56619-909-4"],
            "asin": ["B01N5FIA8V", "B00EXAMPLE"]
        }
        
        # Create DataFrame
        df = pd.DataFrame(template_data)
        
        # Ask user where to save the file
        filetypes = [("CSV files", "*.csv")] if template_type == "csv" else [("Excel files", "*.xlsx")]
        default_extension = ".csv" if template_type == "csv" else ".xlsx"
        
        save_path = filedialog.asksaveasfilename(
            defaultextension=default_extension,
            filetypes=filetypes,
            title=f"Save {template_type.upper()} Template"
        )
        
        if not save_path:
            return
        
        try:
            # Save file based on type
            if template_type == "csv":
                df.to_csv(save_path, index=False)
            else:  # excel
                df.to_excel(save_path, index=False)
            
            messagebox.showinfo("Template Downloaded", f"Template has been saved to:\n{save_path}")
            
            # Ask if user wants to open the file
            if messagebox.askyesno("Open Template", "Would you like to open the template now?"):
                import subprocess
                import platform
                
                system = platform.system()
                if system == 'Darwin':  # macOS
                    subprocess.call(('open', save_path))
                elif system == 'Windows':
                    os.startfile(save_path)
                else:  # Linux
                    subprocess.call(('xdg-open', save_path))
                    
        except Exception as e:
            logger.log_error(f"Error creating template: {str(e)}")
            messagebox.showerror("Error", f"Failed to create template: {str(e)}")
