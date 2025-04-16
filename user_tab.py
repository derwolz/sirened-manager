import tkinter as tk
from tkinter import ttk, messagebox

class UsersTab:
    def __init__(self, parent):
        self.parent = parent
        
        # Create tab
        self.frame = ttk.Frame(parent.notebook)
        parent.notebook.add(self.frame, text="Publisher")
        
        self.setup_tab()
    
    def setup_tab(self):
        # Publisher Details Frame
        publisher_frame = ttk.LabelFrame(self.frame, text="Publisher Profile")
        publisher_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Publisher Name
        ttk.Label(publisher_frame, text="Publisher Name:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.publisher_name_var = tk.StringVar()
        ttk.Entry(publisher_frame, textvariable=self.publisher_name_var, width=50).grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Business Email
        ttk.Label(publisher_frame, text="Business Email:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        self.business_email_var = tk.StringVar()
        ttk.Entry(publisher_frame, textvariable=self.business_email_var, width=50).grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Business Phone
        ttk.Label(publisher_frame, text="Business Phone:").grid(row=2, column=0, sticky=tk.W, pady=5, padx=5)
        self.business_phone_var = tk.StringVar()
        ttk.Entry(publisher_frame, textvariable=self.business_phone_var, width=50).grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Website
        ttk.Label(publisher_frame, text="Website:").grid(row=3, column=0, sticky=tk.W, pady=5, padx=5)
        self.website_var = tk.StringVar()
        ttk.Entry(publisher_frame, textvariable=self.website_var, width=50).grid(row=3, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Description
        ttk.Label(publisher_frame, text="Description:").grid(row=4, column=0, sticky=tk.W, pady=5, padx=5)
        self.description_text = tk.Text(publisher_frame, width=50, height=5)
        self.description_text.grid(row=4, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Save Button
        ttk.Button(publisher_frame, text="Save Profile", command=self.save_publisher_profile).grid(
            row=5, column=0, columnspan=2, pady=10
        )
    
    def load_publisher_data(self):
        """Load publisher data from settings"""
        # Retrieve publisher details from settings or database
        self.publisher_name_var.set(
            self.parent.db_manager.settings.get("publisher_name", "")
        )
        self.business_email_var.set(
            self.parent.db_manager.settings.get("publisher_email", "")
        )
        self.business_phone_var.set(
            self.parent.db_manager.settings.get("publisher_phone", "")
        )
        self.website_var.set(
            self.parent.db_manager.settings.get("publisher_website", "")
        )
        
        # Load description
        description = self.parent.db_manager.settings.get("publisher_description", "")
        self.description_text.delete("1.0", tk.END)
        self.description_text.insert("1.0", description)
    
    def save_publisher_profile(self):
        """Save publisher profile details"""
        try:
            # Save details to settings
            settings_to_save = {
                "publisher_name": self.publisher_name_var.get(),
                "publisher_email": self.business_email_var.get(),
                "publisher_phone": self.business_phone_var.get(),
                "publisher_website": self.website_var.get(),
                "publisher_description": self.description_text.get("1.0", tk.END).strip()
            }
            
            # Save each setting
            for key, value in settings_to_save.items():
                self.parent.db_manager.settings.set(key, value)
            
            messagebox.showinfo("Success", "Publisher profile saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save publisher profile: {str(e)}")
