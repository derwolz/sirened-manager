# book_import/import_dialog.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from datetime import datetime
import app_logger as logger
from .file_handlers import FileHandler
from .data_processor import DataProcessor
from .template_generator import TemplateGenerator

class BooksMassImport:
    def __init__(self, parent_tab):
        self.parent_tab = parent_tab
        self.parent = parent_tab.parent  # Main app reference
        self.db_manager = self.parent.db_manager if hasattr(self.parent, 'db_manager') else None
        self.file_handler = FileHandler()
        self.data_processor = DataProcessor(self.parent)
        self.template_generator = TemplateGenerator()
        
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
        ttk.Button(template_frame, text="Download CSV Template", command=lambda: self.template_generator.download_template("csv")).pack(side=tk.LEFT, padx=5)
        ttk.Button(template_frame, text="Download Excel Template", command=lambda: self.template_generator.download_template("excel")).pack(side=tk.LEFT, padx=5)
        
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
        filetypes = self.file_handler.get_file_types(file_format)
        
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
            
            # Load file data
            headers, first_row = self.file_handler.read_file_headers(
                file_path, 
                file_format, 
                self.skip_header_var.get()
            )
            
            if not headers:
                raise ValueError("Could not read file headers")
            
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
            data = self.data_processor.load_and_transform_data(
                file_path,
                self.file_format_var.get(),
                self.skip_header_var.get(),
                self.mapping_vars
            )
            
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
                validation_issues = self.data_processor.validate_import_data(
                    data, self.update_existing_var.get()
                )
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
    
    def process_import(self):
        """Process the actual import of books"""
        file_path = self.file_path_var.get()
        
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Error", "Please select a valid file")
            return
        
        try:
            # Load and transform the data
            data = self.data_processor.load_and_transform_data(
                file_path,
                self.file_format_var.get(),
                self.skip_header_var.get(),
                self.mapping_vars
            )
            
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
            
            # Import the books
            import_results = self.data_processor.import_books(
                data, 
                self.update_existing_var.get(),
                progress_callback=lambda current, total: [
                    self.progress_var.set((current / total) * 100),
                    self.status_var.set(f"Importing book {current} of {total}: {data[current-1].get('title')}"),
                    self.import_dialog.update_idletasks()
                ]
            )
            
            books_added = import_results['added']
            books_updated = import_results['updated']
            books_skipped = import_results['skipped']
            
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
