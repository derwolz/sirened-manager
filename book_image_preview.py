import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import io
from utils import parse_dimensions
import app_logger as logger

class BookImagePreview:
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.current_book_id = None
        self.image_labels = {}
        self.image_tk_refs = {}  # Keep references to prevent garbage collection
        
        # Create preview frame
        self.preview_frame = ttk.LabelFrame(parent_frame, text="Image Previews")
        self.preview_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        
        # Scrollable frame for images
        self.canvas = tk.Canvas(self.preview_frame, width=150)
        self.scrollbar = ttk.Scrollbar(self.preview_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Frame inside canvas for images
        self.images_frame = ttk.Frame(self.canvas)
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.images_frame, anchor="nw")
        
        # Configure canvas scrolling
        self.images_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Image types from utils.py
        self.image_types = [
            "Grid-item (56x212)",
            "Book-detail (480x600)",
            "Background (1300x1500)",
            "Card (256x440)",
            "Mini (48x64)",
            "Hero (1500x600)"
        ]
        
        # Setup image frames
        self._setup_image_frames()
    
    def _setup_image_frames(self):
        """Create frames for each image type"""
        for img_type in self.image_types:
            frame = ttk.Frame(self.images_frame)
            frame.pack(fill=tk.X, pady=5, padx=5)
            
            # Extract name without dimensions
            type_name = img_type.split(" (")[0]
            
            # Type label
            ttk.Label(frame, text=type_name, font=("Arial", 9, "bold")).pack(anchor="w")
            
            # Image placeholder
            img_label = ttk.Label(frame)
            img_label.pack(pady=2)
            
            # Store reference
            self.image_labels[type_name] = img_label
    
    def _on_frame_configure(self, event):
        """Update the scrollregion when the frame changes size"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_canvas_configure(self, event):
        """When canvas is resized, resize the frame within it"""
        self.canvas.itemconfig(self.canvas_frame, width=event.width)
    
    def update_previews(self, db_manager, book_id):
        """Update image previews for the selected book"""
        self.current_book_id = book_id
        
        # Clear current images
        for label in self.image_labels.values():
            label.config(image="", text="")
        
        # Reset references
        self.image_tk_refs = {}
        
        if not book_id:
            return
        
        # Get images for this book from database
        try:
            images = db_manager.get_images(book_id)
            logger.log_debug(f"Found {len(images) if images else 0} images for book ID {book_id}")
            
            if not images:
                # No images found message
                for type_name, label in self.image_labels.items():
                    label.config(text=f"No {type_name} image")
                return
            
            # For image type matching
            type_map = {
                "Grid-item": "Grid-item",
                "Book-detail": "Book-detail",
                "Background": "Background",
                "Card": "Card",
                "Mini": "Mini",
                "Hero": "Hero"
            }
            
            # Process each image
            for image_data in images:
                image_id = image_data[0]
                local_path = image_data[8]  # local_file_path is at index 8
                
                if not local_path or not os.path.exists(local_path):
                    logger.log_debug(f"Image {image_id} has no local path or file doesn't exist: {local_path}")
                    continue
                
                # Try to determine image type from dimensions
                try:
                    with Image.open(local_path) as img:
                        width, height = img.size
                        logger.log_debug(f"Image {image_id} dimensions: {width}x{height}")
                        
                        # Find matching image type
                        matched_type = None
                        for img_type in self.image_types:
                            type_width, type_height = parse_dimensions(img_type)
                            
                            # If dimensions match or are very close
                            if (abs(width - type_width) < 5 and abs(height - type_height) < 5):
                                matched_type = img_type.split(" (")[0]
                                break
                        
                        # If we found a match, display the image
                        if matched_type and matched_type in self.image_labels:
                            logger.log_debug(f"Displaying image {image_id} as {matched_type}")
                            self._display_image(local_path, matched_type)
                        else:
                            # Try to guess from filename
                            matched_by_name = False
                            for type_key, type_name in type_map.items():
                                if type_key.lower() in os.path.basename(local_path).lower():
                                    logger.log_debug(f"Matched image {image_id} by filename as {type_name}")
                                    self._display_image(local_path, type_name)
                                    matched_by_name = True
                                    break
                            
                            if not matched_by_name:
                                logger.log_debug(f"Could not match image {image_id} to any type")
                        
                except Exception as e:
                    logger.log_debug(f"Error processing image {image_id}: {str(e)}")
        
        except Exception as e:
            logger.log_debug(f"Error getting images for book {book_id}: {str(e)}")
            for type_name, label in self.image_labels.items():
                label.config(text=f"Error loading images")
    
    def _display_image(self, image_path, type_name):
        """Display a scaled image for the given type"""
        try:
            # Load image with PIL
            with Image.open(image_path) as img:
                # Scale to 128px width while maintaining aspect ratio
                width, height = img.size
                new_width = 128
                new_height = int((height / width) * new_width)
                
                # Resize using LANCZOS for better quality
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                img_tk = ImageTk.PhotoImage(img_resized)
                
                # Update label
                self.image_labels[type_name].config(image=img_tk, text="")
                
                # Keep reference to prevent garbage collection
                self.image_tk_refs[type_name] = img_tk
                
        except Exception as e:
            logger.log_debug(f"Error displaying image for {type_name}: {str(e)}")
            self.image_labels[type_name].config(text=f"Error loading {type_name}")
