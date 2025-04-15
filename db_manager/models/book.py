# database/models/book.py
import json
import app_logger as logger
from exceptions import InvalidDataError, DataIntegrityError, EntityNotFoundError

class BookModel:
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
    
    def add(self, book_data):
        """Add a book with specified ID"""
        if not book_data:
            raise InvalidDataError("Book data cannot be None or empty")
            
        if not book_data.get('title'):
            raise InvalidDataError("Book must have a title")
        
        # Format complex fields
        for field in ['formats', 'awards', 'characters', 'referralLinks', 'images']:
            book_data[field] = self._format_json_field(book_data.get(field, ""))
        
        query = """
        INSERT INTO books (
            id, title, author, authorId, description, authorImageUrl,
            promoted, pageCount, formats, publishedDate, awards,
            originalTitle, series, setting, characters, isbn, asin,
            language, referralLinks, impressionCount, clickThroughCount,
            lastImpressionAt, lastClickThroughAt, internal_details, images
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            book_data.get('id'),
            book_data.get('title'),
            book_data.get('author'),
            book_data.get('authorId'),
            book_data.get('description'),
            book_data.get('authorImageUrl'),
            1 if book_data.get('promoted') else 0,
            book_data.get('pageCount'),
            book_data['formats'],
            book_data.get('publishedDate'),
            book_data['awards'],
            book_data.get('originalTitle'),
            book_data.get('series'),
            book_data.get('setting'),
            book_data['characters'],
            book_data.get('isbn'),
            book_data.get('asin'),
            book_data.get('language'),
            book_data['referralLinks'],
            book_data.get('impressionCount'),
            book_data.get('clickThroughCount'),
            book_data.get('lastImpressionAt'),
            book_data.get('lastClickThroughAt'),
            book_data.get('internal_details'),
            book_data['images']
        )
        
        return self.connection_manager.execute(query, params)
    
    def _format_json_field(self, value):
        """Helper method to format JSON fields consistently"""
        if isinstance(value, (list, dict)):
            return json.dumps(value)
        return value or ""
    
    def update(self, book_id, book_data):
        """Update a book"""
        for field in ['formats', 'awards', 'characters', 'referralLinks', 'images']:
            book_data[field] = self._format_json_field(book_data.get(field, ""))
        
        query = """
        UPDATE books SET
            title = ?, author = ?, authorId = ?, description = ?,
            authorImageUrl = ?, promoted = ?, pageCount = ?, formats = ?,
            publishedDate = ?, awards = ?, originalTitle = ?, series = ?,
            setting = ?, characters = ?, isbn = ?, asin = ?, language = ?,
            referralLinks = ?, impressionCount = ?, clickThroughCount = ?,
            lastImpressionAt = ?, lastClickThroughAt = ?, 
            internal_details = ?, images = ?
        WHERE id = ?
        """
        
        params = (
            book_data.get('title'),
            book_data.get('author'),
            book_data.get('authorId'),
            book_data.get('description'),
            book_data.get('authorImageUrl'),
            1 if book_data.get('promoted') else 0,
            book_data.get('pageCount'),
            book_data['formats'],
            book_data.get('publishedDate'),
            book_data['awards'],
            book_data.get('originalTitle'),
            book_data.get('series'),
            book_data.get('setting'),
            book_data['characters'],
            book_data.get('isbn'),
            book_data.get('asin'),
            book_data.get('language'),
            book_data['referralLinks'],
            book_data.get('impressionCount'),
            book_data.get('clickThroughCount'),
            book_data.get('lastImpressionAt'),
            book_data.get('lastClickThroughAt'),
            book_data.get('internal_details'),
            book_data['images'],
            book_id
        )
        
        return self.connection_manager.execute(query, params)
    
    def get_all(self):
        """Get all books with author names"""
        query = """
        SELECT b.*, a.author_name,
               CASE WHEN b.author IS NOT NULL AND b.author != '' THEN b.author 
                    WHEN a.author_name IS NOT NULL THEN a.author_name 
                    ELSE '' END AS effective_author
        FROM books b 
        LEFT JOIN authors a ON b.authorId = a.id
        ORDER BY b.title
        """
        return self.connection_manager.execute(query)
    
    def get(self, book_id):
        """Get a book by ID"""
        results = self.connection_manager.execute(
            "SELECT * FROM books WHERE id = ?", 
            (book_id,)
        )
        if not results:
            raise EntityNotFoundError(f"Book with ID {book_id} not found")
        return results[0]
    
    def get_by_author(self, author_id):
        """Get all books by an author"""
        return self.connection_manager.execute(
            "SELECT * FROM books WHERE authorId = ?", 
            (author_id,)
        )
