import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from PIL import Image, ImageTk

class ImagesTab:
    def __init__(self, parent):
        self.parent = parent
        
        # Create tab
        self.frame = ttk.Frame(parent.notebook)
        parent.notebook.add(self.frame, text="Images")
        
        self.setup_tab()
    
    def setup_tab(self):
        # Images list frame (left side)
        images_list_frame = ttk.Frame(self.frame)
        images_list_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10)
        
        # Images list
        ttk.Label(images_list_frame, text="Image Entries:").pack(anchor=tk.W)
        self.images_listbox = tk.Listbox(images_list_frame, width=30, height=20)
        self.images_listbox.pack(fill=tk.BOTH, expand=True)
        self.images_listbox.bind('<<ListboxSelect>>', self.on_image_select)
        
        # Buttons for image management
        btn_frame = ttk.Frame(images_list_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Add New", command=self.add_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete", command=self.delete_image).pack(side=tk.LEFT, padx=5)
        
        # Image details frame (right side)
        self.image_details_frame = ttk.Frame(self.frame)
        self.image_details_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Item type selection
        ttk.Label(self.image_details_frame, text="Item Type*:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.image_item_type_var = tk.StringVar(value="Book")
        item_type_frame = ttk.Frame(self.image_details_frame)
        item_type_frame.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(item_type_frame, text="Book", variable=self.image_item_type_var, value="Book", command=self.toggle_image_type).pack(side=tk.LEFT)
        self.author_radio = ttk.Radiobutton(item_type_frame, text="Author", variable=self.image_item_type_var, value="Author", command=self.toggle_image_type)
        self.author_radio.pack(side=tk.LEFT)
        
        # Item selection
        ttk.Label(self.image_details_frame, text="Select Item*:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.image_item_var = tk.StringVar()
        self.image_item_combo = ttk.Combobox(self.image_details_frame, textvariable=self.image_item_var, width=38)
        self.image_item_combo.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Image type selection
        ttk.Label(self.image_details_frame, text="Image Type*:").grid(row=2, column=0, sticky=tk.W, pady=5)
        
        # Book image types frame
        self.book_image_types_frame = ttk.Frame(self.image_details_frame)
        self.book_image_types_frame.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        self.book_image_type_var = tk.StringVar()
        book_image_types = [
            "Grid-item (56x212)", 
            "Book-detail (480x600)",
            "Background (1300x1500)",
            "Card (256x440)",
            "Mini (48x64)",
            "Hero (1500x600)"
        ]
        
        self.book_image_type_combo = ttk.Combobox(self.book_image_types_frame, textvariable=self.book_image_type_var, values=book_image_types, width=38)
        self.book_image_type_combo.pack(fill=tk.X)
        
        # Author image types frame
        self.author_image_types_frame = ttk.Frame(self.image_details_frame)
        self.author_image_types_frame.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        self.author_image_type_var = tk.StringVar(value="Profile pic (128x128)")
        author_image_types = ["Profile pic (128x128)"]
        
        self.author_image_type_combo = ttk.Combobox(self.author_image_types_frame, textvariable=self.author_image_type_var, values=author_image_types, width=38)
        self.author_image_type_combo.pack(fill=tk.X)
        
        # Image file selector
        ttk.Label(self.image_details_frame, text="Image File*:").grid(row=3, column=0, sticky=tk.W, pady=5)
        file_frame = ttk.Frame(self.image_details_frame)
        file_frame.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        self.image_file_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.image_file_var, width=30).pack(side=tk.LEFT)
        ttk.Button(file_frame, text="Browse", command=self.browse_image).pack(side=tk.LEFT, padx=5)
        
        # Image preview
        self.image_preview_frame = ttk.LabelFrame(self.image_details_frame, text="Image Preview")
        self.image_preview_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        self.image_preview = ttk.Label(self.image_preview_frame)
        self.image_preview.pack(pady=10)
        
        # Save button
        ttk.Button(self.image_details_frame, text="Save Image", command=self.save_image).grid(
            row=5, column=0, columnspan=2, pady=10
        )
        
        # Hide author image types by default
        self.author_image_types_frame.grid_remove()
    
    def toggle_image_type(self):
        """Toggle between book and author image options"""
        item_type = self.image_item_type_var.get()
        
        if item_type == "Book":
            self.book_image_types_frame.grid()
            self.author_image_types_frame.grid_remove()
        else:
            self.book_image_types_frame.grid_remove()
            self.author_image_types_frame.grid()
            
        # Update the item dropdown
        self.update_image_item_dropdown()
    
    def update_image_item_dropdown(self):
        """Update item selection dropdown in images tab"""
        item_type = self.image_item_type_var.get()
        
        if item_type == "Book":
            book_titles = [book["title"] for book in self.parent.books]
            self.image_item_combo['values'] = book_titles
        else:
            author_names = [author["author_name"] for author in self.parent.authors]
            self.image_item_combo['values'] = author_names
    
    def add_image(self):
        """Add a new image"""
        self.image_file_var.set("")
        self.image_preview.configure(image="")
    
    def save_image(self):
        """Save current image data"""
        item_type = self.image_item_type_var.get()
        item = self.image_item_var.get()
        
        if not item:
            messagebox.showerror("Error", f"Please select a {item_type.lower()}")
            return
        
        # Verify item exists
        item_exists = False
        if item_type == "Book":
            for b in self.parent.books:
                if b["title"] == item:
                    item_exists = True
                    break
        else:  # Author
            for a in self.parent.authors:
                if a["author_name"] == item:
                    item_exists = True
                    break
        
        if not item_exists:
            messagebox.showerror("Error", f"{item_type} '{item}' doesn't exist")
            return
        
        # Get image type
        if item_type == "Book":
            image_type = self.book_image_type_var.get()
        else:  # Author
            image_type = self.author_image_type_var.get()
        
        if not image_type:
            messagebox.showerror("Error", "Please select an image type")
            return
        
        # Get image file
        image_file = self.image_file_var.get()
        
        if not image_file:
            messagebox.showerror("Error", "Please select an image file")
            return
        
        if not os.path.exists(image_file):
            messagebox.showerror("Error", f"Image file '{image_file}' does not exist")
            return
        
        # Check image dimensions
        try:
            with Image.open(image_file) as img:
                width, height = img.size
                
                # Extract expected dimensions from image type
                if "(" in image_type and ")" in image_type:
                    dim_str = image_type.split("(")[1].split(")")[0]
                    
                    if "x" in dim_str:
                        expected_width, expected_height = map(int, dim_str.split("x"))
                        
                        if width != expected_width or height != expected_height:
                            messagebox.showerror(
                                "Error", 
                                f"Image dimensions ({width}x{height}) do not match the required dimensions ({expected_width}x{expected_height})"
                            )
                            return
        except Exception as e:
            messagebox.showerror("Error", f"Failed to check image dimensions: {str(e)}")
            return
        
        # Create image data
        image_data = {
            "item_type": item_type,
            "item": item,
            "image_type": image_type.split(" (")[0],  # Remove dimensions part
            "file_path": image_file
        }
        
        # Check if image already exists (same item and image type)
        image_index = None
        for i, img in enumerate(self.parent.images):
            if img["item_type"] == item_type and img["item"] == item and img["image_type"] == image_data["image_type"]:
                image_index = i
                break
        
        if image_index is not None:
            # Update existing image
            self.parent.images[image_index] = image_data
        else:
            # Add new image
            self.parent.images.append(image_data)
        
        # Update UI
        self.update_images_listbox()
        self.parent.update_export_status()
        
        messagebox.showinfo("Success", f"Image for {item_type.lower()} '{item}' saved successfully")
    
    def delete_image(self):
        """Delete the selected image"""
        selected_indices = self.images_listbox.curselection()
        
        if not selected_indices:
            messagebox.showerror("Error", "No image selected")
            return
        
        index = selected_indices[0]
        if index < len(self.parent.images):
            image = self.parent.images[index]
            
            del self.parent.images[index]
            self.update_images_listbox()
            
            self.image_file_var.set("")
            self.image_preview.configure(image="")
            self.parent.update_export_status()
            
            messagebox.showinfo(
                "Success", 
                f"Image for {image['item_type'].lower()} '{image['item']}' deleted successfully"
            )
    
    def on_image_select(self, event):
        """Handle image selection"""
        selected_indices = self.images_listbox.curselection()
        
        if not selected_indices:
            return
        
        index = selected_indices[0]
        if index < len(self.parent.images):
            image = self.parent.images[index]
            
            # Set item type
            self.image_item_type_var.set(image["item_type"])
            self.toggle_image_type()
            
            # Set item
            self.image_item_var.set(image["item"])
            
            # Set image type
            if image["item_type"] == "Book":
                # Find the combo value that contains the image type
                for value in self.book_image_type_combo["values"]:
                    if value.startswith(image["image_type"]):
                        self.book_image_type_var.set(value)
                        break
            else:
                for value in self.author_image_type_combo["values"]:
                    if value.startswith(image["image_type"]):
                        self.author_image_type_var.set(value)
                        break
            
            # Set image file
            self.image_file_var.set(image["file_path"])
            
            # Preview image
            self.preview_image()
    
    def update_images_listbox(self):
        """Update the images listbox"""
        self.images_listbox.delete(0, tk.END)
        
        for image in self.parent.images:
            self.images_listbox.insert(
                tk.END, 
                f"{image['item_type']}: {image['item']} - {image['image_type']}"
            )
    
    def browse_image(self):
        """Browse for an image file"""
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif")]
        )
        
        if file_path:
            self.image_file_var.set(file_path)
            self.preview_image()
    
    def preview_image(self):
        """Preview the selected image"""
        file_path = self.image_file_var.get()
        
        if not file_path or not os.path.exists(file_path):
            return
        
        try:
            image = Image.open(file_path)
            
            # Resize for preview (maintaining aspect ratio)
            width, height = image.size
            max_size = 200
            
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))
            
            image = image.resize((new_width, new_height), Image.LANCZOS)
            
            photo = ImageTk.PhotoImage(image)
            self.image_preview.configure(image=photo)
            self.image_preview.image = photo  # Keep a reference
            
            # Update preview frame text
            if self.image_item_type_var.get() == "Book":
                image_type = self.book_image_type_var.get()
            else:
                image_type = self.author_image_type_var.get()
                
            self.image_preview_frame.configure(text=f"Image Preview - Original: {width}x{height}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to preview image: {str(e)}")
