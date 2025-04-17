# book_import/template_generator.py

import os
import pandas as pd
import subprocess
import platform
import app_logger as logger
from tkinter import filedialog, messagebox

class TemplateGenerator:
    """Generates template files for book import"""
    
    def __init__(self):
        """Initialize template generator"""
        pass
        
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
                self._open_file(save_path)
                    
        except Exception as e:
            logger.log_error(f"Error creating template: {str(e)}")
            messagebox.showerror("Error", f"Failed to create template: {str(e)}")
    
    def _open_file(self, file_path):
        """Open a file using the default system application"""
        try:
            system = platform.system()
            if system == 'Darwin':  # macOS
                subprocess.call(('open', file_path))
            elif system == 'Windows':
                os.startfile(file_path)
            else:  # Linux
                subprocess.call(('xdg-open', file_path))
        except Exception as e:
            logger.log_error(f"Error opening file: {str(e)}")
            messagebox.showerror("Error", f"Failed to open file: {str(e)}")
