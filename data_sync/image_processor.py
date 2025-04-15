"""
Image processing and download functionality.
"""

import app_logger as logger
from image_downloader import ImageDownloader

class ImageProcessor:
    """
    Handles processing and downloading images
    """
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.image_downloader = ImageDownloader(db_manager)
        
    def download_all_images(self):
        """Download all author and book images"""
        author_results = self.image_downloader.batch_download_author_images()
        book_results = self.image_downloader.batch_download_book_images()
    
        results = {
            'authors': author_results,
            'books': book_results,
            'total_success': author_results['success'] + book_results['success'],
            'total_failed': author_results['failed'] + book_results['failed']
        }
        
        return results
        
    def download_author_image(self, author_id, image_url):
        """Download an author's profile image"""
        return self.image_downloader.download_author_image(author_id, image_url)
        
    def download_book_image(self, book_id, image_url, image_id=None):
        """Download a book image"""
        return self.image_downloader.download_book_image(book_id, image_url, image_id)
    
    def process_book_images(self, images, book_id):
        """Process and store book images in the database"""
        if not images:
            return
        
        # Find local book ID
        book_local_id_setting = self.db_manager.get_setting(f"book_api_id_{book_id}")
        if not book_local_id_setting:
            logger.log_warning(f"Could not find local book ID for remote book ID {book_id}")
            return
        
        book_local_id = int(book_local_id_setting)
        
        for image in images:
            image_id = image.get("id")
            image_url = image.get("imageUrl", "")
            image_type = image.get("imageType", "")
            width = image.get("width")
            height = image.get("height")
            size_kb = image.get("sizeKb")
            
            # Check if image already exists
            existing_images = self.db_manager.execute_query(
                "SELECT id FROM images WHERE bookId = ? AND imageUrl = ?",
                (book_local_id, image_url)
            )
            
            local_image_id = None
            
            if existing_images:
                # Update existing image
                local_image_id = existing_images[0][0]
                self.db_manager.update_image(local_image_id, {
                    'remote_url': image_url,
                    'width': width,
                    'height': height,
                    'sizeKb': size_kb
                })
            else:
                # Insert new image record
                local_image_id = self.db_manager.add_image({
                    'bookId': book_local_id,
                    'imageUrl': image_url,
                    'width': width,
                    'height': height,
                    'sizeKb': size_kb
                })
            
            # Download the image if URL is provided
            if image_url and local_image_id:
                self.download_book_image(book_local_id, image_url, local_image_id)

