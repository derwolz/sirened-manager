import os
import re
import datetime
from PIL import Image

def validate_date_format(date_str):
    """
    Validate that the date string is in YYYY-MM-DD format
    Returns True if valid, False otherwise
    """
    if not date_str:
        return True  # Empty string is allowed (optional dates)
    
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", date_str))

def validate_image_dimensions(image_path, expected_width, expected_height):
    """
    Validate that the image has the expected dimensions
    Returns (True, None) if valid, (False, error_message) otherwise
    """
    try:
        if not os.path.exists(image_path):
            return False, f"Image file doesn't exist: {image_path}"
            
        with Image.open(image_path) as img:
            width, height = img.size
            
            if width != expected_width or height != expected_height:
                return False, f"Image dimensions ({width}x{height}) do not match the required dimensions ({expected_width}x{expected_height})"
            
            return True, None
    except Exception as e:
        return False, f"Error checking image: {str(e)}"

def parse_dimensions(type_string):
    """
    Extract dimensions from a string like "Grid-item (56x212)"
    Returns (width, height) tuple or None if not found
    """
    if "(" in type_string and ")" in type_string:
        dim_str = type_string.split("(")[1].split(")")[0]
        
        if "x" in dim_str:
            try:
                width, height = map(int, dim_str.split("x"))
                return width, height
            except ValueError:
                pass
    
    return None, None

def sanitize_filename(filename):
    """
    Convert a string to a safe filename
    """
    # Replace spaces with underscores
    filename = filename.replace(" ", "_")
    # Remove any characters that aren't alphanumeric, underscore, or dash
    filename = re.sub(r'[^\w\-\.]', '', filename)
    return filename

def get_book_image_types():
    """
    Return a list of book image types with dimensions
    """
    return [
        "Grid-item (56x212)", 
        "Book-detail (480x600)",
        "Background (1300x1500)",
        "Card (256x440)",
        "Mini (48x64)",
        "Hero (1500x600)"
    ]

def get_author_image_types():
    """
    Return a list of author image types with dimensions
    """
    return ["Profile pic (128x128)"]

def generate_timestamp():
    """
    Generate a formatted timestamp for filenames
    """
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
