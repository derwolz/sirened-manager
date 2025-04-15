import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
from config import API_BASE_URL, LOGIN_ENDPOINT, AUTHOR_STATUS_ENDPOINT, PUBLISHER_STATUS_ENDPOINT
from data_sync import DataSynchronizer

class AuthenticationTab:
    def __init__(self, parent):
        self.parent = parent
        
        # Create tab
        self.frame = ttk.Frame(parent.notebook)
        parent.notebook.add(self.frame, text="Authentication")
        
        # Session state
        self.is_authenticated = tk.BooleanVar(value=False)
        self.session_token = None
        self.cookies = None
        
        self.setup_tab()
    
    def setup_tab(self):
        # Title
        title_label = ttk.Label(
            self.frame,
            text="Login to Your Account",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(20, 10))
        
        # Login frame
        login_frame = ttk.Frame(self.frame)
        login_frame.pack(pady=10, padx=20, fill="x")
        
        # Email/Username field
        email_label = ttk.Label(login_frame, text="Email or Username:")
        email_label.grid(row=0, column=0, sticky="w", pady=5)
        self.email_entry = ttk.Entry(login_frame, width=30)
        self.email_entry.grid(row=0, column=1, pady=5, padx=5, sticky="ew")
        
        # Password field
        password_label = ttk.Label(login_frame, text="Password:")
        password_label.grid(row=1, column=0, sticky="w", pady=5)
        self.password_entry = ttk.Entry(login_frame, width=30, show="*")
        self.password_entry.grid(row=1, column=1, pady=5, padx=5, sticky="ew")
        
        # Login button
        login_button = ttk.Button(login_frame, text="Login", command=self.login)
        login_button.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Status frame
        self.status_frame = ttk.LabelFrame(self.frame, text="Session Status")
        self.status_frame.pack(pady=10, padx=20, fill="x")
        
        # Status labels
        self.auth_status_label = ttk.Label(
            self.status_frame,
            text="Not authenticated",
            foreground="red"
        )
        self.auth_status_label.pack(pady=(10, 5))
        
        # Add sync status label
        self.sync_status_label = ttk.Label(
            self.status_frame,
            text="Data synchronization: Not started",
            foreground="gray"
        )
        self.sync_status_label.pack(pady=2)
        
        self.author_status_label = ttk.Label(
            self.status_frame,
            text="Author status: Unknown",
            foreground="gray"
        )
        self.author_status_label.pack(pady=2)
        
        self.publisher_status_label = ttk.Label(
            self.status_frame,
            text="Publisher status: Unknown",
            foreground="gray"
        )
        self.publisher_status_label.pack(pady=(2, 10))
        
        # Logout button (initially disabled)
        self.logout_button = ttk.Button(
            self.status_frame, 
            text="Logout", 
            command=self.logout,
            state="disabled"
        )
        self.logout_button.pack(pady=(0, 10))
        
        # Configure grid
        login_frame.columnconfigure(1, weight=1)
    
    def login(self):
        # Get credentials
        email = str(self.email_entry.get()).lower()
        password = self.password_entry.get()
        
        # Validate inputs
        if not email or not password:
            messagebox.showerror("Error", "Please enter both email/username and password")
            return
        
        # Prepare the login request
        url = f"{API_BASE_URL}{LOGIN_ENDPOINT}"
        headers = {"Content-Type": "application/json"}
        data = {"email": email, "password": password}
        
        try:
            # Send the login request
            response = requests.post(url, headers=headers, data=json.dumps(data))
            
            # Check if login was successful
            if response.status_code == 200:
                self.cookies = response.cookies
                self.is_authenticated.set(True)
                
                # Update UI
                self.auth_status_label.config(text="Authenticated", foreground="green")
                self.logout_button.config(state="normal")
                
                # Save cookies in parent for other tabs to use
                self.parent.cookies = self.cookies
                self.parent.is_authenticated = self.is_authenticated
                
                # Check author and publisher status
                self.check_author_status()
                self.check_publisher_status()
                
                # Synchronize data from the API to local database
                try:
                    self.sync_status_label.config(text="Synchronizing data...", foreground="blue")
                    self.frame.update_idletasks()  # Force UI update
                    
                    synchronizer = DataSynchronizer(self.parent.db_manager, self.parent)
                    sync_success = synchronizer.synchronize_data(self.cookies)
                    
                    if sync_success:
                        self.sync_status_label.config(text="Data synchronized successfully", foreground="green")
                    else:
                        self.sync_status_label.config(text="Data synchronization failed", foreground="red")
                except Exception as e:
                    print(f"Error during data synchronization: {str(e)}")
                    self.sync_status_label.config(text="Data synchronization error", foreground="red")
                
                messagebox.showinfo("Success", "Login successful!")
                
                # Clear password field for security
                self.password_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Login Failed", f"Error: {response.status_code}\n{response.text}")
        
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to server: {str(e)}")
    
    def check_author_status(self):
        """Check if the current user is an author"""
        url = f"{API_BASE_URL}{AUTHOR_STATUS_ENDPOINT}"
        
        try:
            response = requests.get(url, cookies=self.cookies)
            
            if response.status_code == 200:
                data = response.json()
                is_author = data.get("isAuthor", False)
                
                # Update parent's state
                self.parent.is_author.set(is_author)
                
                # Store author details if available
                if is_author and "authorDetails" in data:
                    self.parent.author_details = data["authorDetails"]
                
                # Update UI
                if is_author:
                    self.author_status_label.config(
                        text="Author status: Yes", 
                        foreground="green"
                    )
                else:
                    self.author_status_label.config(
                        text="Author status: No", 
                        foreground="blue"
                    )
            else:
                self.author_status_label.config(
                    text="Author status: Error checking", 
                    foreground="red"
                )
        
        except Exception as e:
            self.author_status_label.config(
                text="Author status: Error checking", 
                foreground="red"
            )
            print(f"Error checking author status: {str(e)}")
    
    def check_publisher_status(self):
        """Check if the current user is a publisher"""
        url = f"{API_BASE_URL}{PUBLISHER_STATUS_ENDPOINT}"
        
        try:
            response = requests.get(url, cookies=self.cookies)
            
            if response.status_code == 200:
                data = response.json()
                is_publisher = data.get("isPublisher", False)
                
                # Update parent's state and UI
                self.parent.is_publisher.set(is_publisher)
                
                # Store publisher details if available
                if is_publisher and "publisherDetails" in data:
                    self.parent.publisher_details = data["publisherDetails"]
                
                # Update UI
                if is_publisher:
                    self.publisher_status_label.config(
                        text="Publisher status: Yes", 
                        foreground="green"
                    )
                else:
                    self.publisher_status_label.config(
                        text="Publisher status: No", 
                        foreground="blue"
                    )
                
                # Update publisher mode in the application
                if hasattr(self.parent, 'toggle_publisher_mode'):
                    self.parent.toggle_publisher_mode()
            else:
                self.publisher_status_label.config(
                    text="Publisher status: Error checking", 
                    foreground="red"
                )
        
        except Exception as e:
            self.publisher_status_label.config(
                text="Publisher status: Error checking", 
                foreground="red"
            )
            print(f"Error checking publisher status: {str(e)}")
    
    def logout(self):
        # Reset authentication state
        self.is_authenticated.set(False)
        self.cookies = None
        
        # Update parent state
        self.parent.cookies = None
        self.parent.is_authenticated = self.is_authenticated
        
        # Reset author and publisher status
        self.parent.is_author.set(False)
        self.parent.is_publisher.set(False)
        
        # Clear stored details
        if hasattr(self.parent, 'author_details'):
            delattr(self.parent, 'author_details')
        if hasattr(self.parent, 'publisher_details'):
            delattr(self.parent, 'publisher_details')
        
        # Update UI
        self.auth_status_label.config(text="Not authenticated", foreground="red")
        self.sync_status_label.config(text="Data synchronization: Not started", foreground="gray")
        self.author_status_label.config(text="Author status: Unknown", foreground="gray")
        self.publisher_status_label.config(text="Publisher status: Unknown", foreground="gray")
        self.logout_button.config(state="disabled")
        
        messagebox.showinfo("Logged Out", "You have successfully logged out")
