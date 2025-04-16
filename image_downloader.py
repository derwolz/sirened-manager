import os
import requests
import shutil
from urllib.parse import urlparse
import app_logger as logger
from config import API_BASE_URL
from PIL import Image

class ImageDownloader:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        # Ensure base upload directory exists
        self.base_path = os.path.abspath("./")
        
        # Create base directory if it doesn't exist
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)
            logger.log_debug(f"Created base directory: {self.base_path}")
    
    def download_image(self, url, save_path=None):
        """
        Download an image from a URL and save it to the specified path
        
        Args:
            url (str): The URL of the image to download
            save_path (str, optional): The full path where the image should be saved.
                                      If None, it will be determined from the URL.
                
        Returns:
            str: The local path where the image was saved if successful, None otherwise
        """
        try:
            # Validate URL
            logger.log_debug(f"Attempting to download image from: {url}")
            
            # If no save_path is provided, create one from the URL
            if not save_path:
                # Extract the path from the URL
                parsed_url = urlparse(url)
                path = parsed_url.path
                
                # Create the full save path preserving the URL structure
                save_path = os.path.join(self.base_path, path.lstrip('/'))
            
            # Create directory structure for the image if it doesn't exist
            save_dir = os.path.dirname(save_path)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
                logger.log_debug(f"Created directory structure for image: {save_dir}")
            
            # Download the image with timeout and headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Try with stream first
            logger.log_debug(f"Starting download with stream=True")

            full_url = f"{API_BASE_URL}/{url}" if not url.startswith(('http://', 'https://')) else url
            response = requests.get(full_url, stream=True, headers=headers, timeout=30)
            
            if response.status_code != 200:
                # Try with API_BASE_URL prefix as fallback
                logger.log_debug(f"First attempt failed, trying with API_BASE_URL: {full_url}")
                response = requests.get(full_url, stream=True, headers=headers, timeout=30)
                
                if response.status_code != 200:
                    logger.log_error(f"Failed to download image, status code: {response.status_code}")
                    return None
            
            # Save the image to disk using stream
            with open(save_path, 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
            
            # Verify the file was created and has content
            if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                logger.log_debug(f"Image successfully downloaded to {save_path}")
                return save_path
            else:
                logger.log_error(f"File created but has no content: {save_path}")
                return None
                
        except requests.exceptions.Timeout:
            logger.log_error(f"Timeout downloading image from {url}")
            return None
        except requests.exceptions.ConnectionError:
            logger.log_error(f"Connection error downloading image from {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.log_error(f"Request exception downloading image from {url}: {str(e)}")
            return None
        except Exception as e:
            logger.log_error(f"Unexpected error downloading image from {url}: {str(e)}")
            return None

    def download_author_image(self, author_id, image_url):
        """
        Download an author's profile picture, preserving the original URL path
        
        Args:
            author_id (int): The author's ID
            image_url (str): The URL of the author's profile picture
            
        Returns:
            str: Local file path if successful, None otherwise
        """
        full_url = f"{API_BASE_URL}/{image_url}"
        if not image_url:
            
            logger.log_debug(f"No image URL provided for author {author_id}")
            return None
        
        # Log the author and image URL
        logger.log_debug(f"Downloading author image for author_id={author_id}, URL={full_url}")
        
        # Download the image preserving URL structure
        local_path = self.download_image(full_url)
        
        if local_path:
            # Update the author record with the local file path
            try:
                author = self.db_manager.authors.get_all(author_id)
                if author:
                    update_data = {
                        'local_image_path': local_path
                    }
                    logger.log_debug(f"Updating author with local_image_path: {local_path}")
                    self.db_manager.authors.update(author_id, update_data)
                return local_path
            except Exception as e:
                logger.log_error(f"Error updating author with local image path: {str(e)}")
                return local_path  # Still return the path even if DB update fails
        return None

    def download_book_image(self, book_id, image_url, image_id=None):
        """
        Download a book image, preserving the original URL path
        
        Args:
            book_id (int): The book's ID
            image_url (str): The URL of the book image
            image_id (int, optional): The image ID if available
            
        Returns:
            str: Local file path if successful, None otherwise
        """
        full_url = f"{API_BASE_URL}/{image_url}"
        if not image_url:
            logger.log_debug(f"No image URL provided for book {book_id}")
            return None
        
        # Log the book and image URL
        logger.log_debug(f"Downloading book image for book_id={book_id}, image_id={image_id}, URL={full_url}")
        
        # Download the image preserving URL structure
        local_path = self.download_image(full_url)
        
        if local_path:
            # Update the image record with the local file path if image_id is provided
            try:
                if image_id:
                    update_data = {
                        'local_file_path': local_path
                    }
                    logger.log_debug(f"Updating image record with local_file_path: {local_path}")
                    self.db_manager.images.update(image_id, update_data)
                return local_path
            except Exception as e:
                logger.log_error(f"Error updating image record with local file path: {str(e)}")
                return local_path  # Still return the path even if DB update fails
        return None

    def batch_download_author_images(self):
        """
        Download images for all authors in the database
        
        Returns:
            dict: A dictionary containing success and failure counts and details
        """
        results = {
            'success': 0,
            'failed': 0,
            'successful_authors': [],
            'failed_authors': []
        }
        
        try:
            # Get all authors with image URLs that need downloading
            authors = self.db_manager.execute_query(
                """
                SELECT id, author_name, author_image_url 
                FROM authors 
                WHERE author_image_url IS NOT NULL 
                AND (local_image_path IS NULL OR local_image_path = '')
                """
            )
            
            if not authors:
                logger.log_debug("No author images need downloading")
                return results
                
            logger.log_debug(f"Found {len(authors)} authors with images to download")
            
            # Download each author's image
            for author in authors:
                author_id = author[0]
                author_name = author[1]
                image_url = author[2]
                
                if not image_url:
                    continue
                    
                try:
                    logger.log_debug(f"Downloading image for author {author_name} (ID: {author_id})")
                    local_path = self.download_author_image(author_id, image_url)
                    
                    if local_path:
                        results['success'] += 1
                        results['successful_authors'].append({
                            'id': author_id,
                            'name': author_name,
                            'url': image_url,
                            'local_path': local_path
                        })
                        logger.log_debug(f"Successfully downloaded image for author {author_name}")
                    else:
                        results['failed'] += 1
                        results['failed_authors'].append({
                            'id': author_id,
                            'name': author_name,
                            'url': image_url,
                            'error': "Download failed"
                        })
                        logger.log_error(f"Failed to download image for author {author_name}")
                except Exception as e:
                    results['failed'] += 1
                    results['failed_authors'].append({
                        'id': author_id,
                        'name': author_name,
                        'url': image_url,
                        'error': str(e)
                    })
                    logger.log_error(f"Error downloading image for author {author_name}: {str(e)}")
                    
            logger.log_debug(f"Author image download complete: {results['success']} successful, {results['failed']} failed")
            return results
            
        except Exception as e:
            logger.log_error(f"Error in batch download of author images: {str(e)}")
            results['error'] = str(e)
            return results

    def batch_download_book_images(self):
        """
        Download images for all books in the database
        
        Returns:
            dict: A dictionary containing success and failure counts and details
        """
        results = {
            'success': 0,
            'failed': 0,
            'successful_books': [],
            'failed_books': []
        }
        
        try:
            # Get all book images that need downloading
            images = self.db_manager.execute_query(
                """
                SELECT i.id, i.bookId, b.title, i.imageUrl 
                FROM images i
                JOIN books b ON i.bookId = b.id
                WHERE i.imageUrl IS NOT NULL 
                AND (i.local_file_path IS NULL OR i.local_file_path = '')
                """
            )
            
            if not images:
                logger.log_debug("No book images need downloading")
                return results
                
            logger.log_debug(f"Found {len(images)} book images to download")
            
            # Download each book image
            for image in images:
                image_id = image[0]
                book_id = image[1]
                book_title = image[2]
                image_url = image[3]
                
                if not image_url:
                    continue
                    
                try:
                    logger.log_debug(f"Downloading image {image_id} for book '{book_title}' (ID: {book_id})")
                    local_path = self.download_book_image(book_id, image_url, image_id)
                    
                    if local_path:
                        # Update image with dimensions
                        try:
                            with Image.open(local_path) as img:
                                width, height = img.size
                                file_size = os.path.getsize(local_path) // 1024  # Size in KB
                                
                                # Update image record with dimensions
                                self.db_manager.images.update(image_id, {
                                    'width': width,
                                    'height': height,
                                    'sizeKb': file_size,
                                    'local_file_path': local_path
                                })
                        except Exception as e:
                            logger.log_error(f"Error analyzing image dimensions: {str(e)}")
                        
                        results['success'] += 1
                        results['successful_books'].append({
                            'image_id': image_id,
                            'book_id': book_id,
                            'title': book_title,
                            'url': image_url,
                            'local_path': local_path
                        })
                        logger.log_debug(f"Successfully downloaded image for book '{book_title}'")
                    else:
                        results['failed'] += 1
                        results['failed_books'].append({
                            'image_id': image_id,
                            'book_id': book_id,
                            'title': book_title,
                            'url': image_url,
                            'error': "Download failed"
                        })
                        logger.log_error(f"Failed to download image for book '{book_title}'")
                except Exception as e:
                    results['failed'] += 1
                    results['failed_books'].append({
                        'image_id': image_id,
                        'book_id': book_id,
                        'title': book_title,
                        'url': image_url,
                        'error': str(e)
                    })
                    logger.log_error(f"Error downloading image for book '{book_title}': {str(e)}")
                    
            logger.log_debug(f"Book image download complete: {results['success']} successful, {results['failed']} failed")
            return results
            
        except Exception as e:
            logger.log_error(f"Error in batch download of book images: {str(e)}")
            results['error'] = str(e)
            return results
