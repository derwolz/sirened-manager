# database/schema.py
"""Database schema initialization"""

def initialize_tables(cursor):
    """Create all database tables if they don't exist"""
    
    # Create publishers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS publishers (
        id INTEGER PRIMARY KEY,
        userId INTEGER,
        name TEXT,
        publisher_name TEXT,
        publisher_description TEXT,
        business_email TEXT,
        business_phone TEXT,
        business_address TEXT,
        description TEXT,
        website TEXT,
        logoUrl TEXT,
        createdAt TIMESTAMP
    )
    ''')
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        email TEXT,
        displayName TEXT
    )
    ''')
    
    # Create authors table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS authors (
        id INTEGER PRIMARY KEY,
        userId INTEGER,
        author_name TEXT,
        author_image_url TEXT,
        birth_date TEXT,
        death_date TEXT,
        website TEXT,
        bio TEXT,
        local_image_path TEXT DEFAULT NULL,
        FOREIGN KEY (userId) REFERENCES users (id)
    )
    ''')
    
    # Create books table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY,
        title TEXT,
        author TEXT,
        authorId INTEGER,
        description TEXT,
        authorImageUrl TEXT,
        promoted BOOLEAN DEFAULT 0,
        pageCount INTEGER,
        formats TEXT,
        publishedDate TEXT,
        awards TEXT,
        originalTitle TEXT,
        series TEXT,
        setting TEXT,
        characters TEXT,
        isbn TEXT,
        asin TEXT,
        language TEXT,
        referralLinks TEXT,
        impressionCount INTEGER,
        clickThroughCount INTEGER,
        lastImpressionAt TIMESTAMP,
        lastClickThroughAt TIMESTAMP,
        internal_details TEXT,
        images TEXT,
        FOREIGN KEY (authorId) REFERENCES authors (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY,
        bookId INTEGER,
        imageUrl TEXT,
        width INTEGER,
        height INTEGER,
        sizeKb INTEGER,
        createdAt TIMESTAMP,
        updatedAt TIMESTAMP,
        local_file_path TEXT DEFAULT NULL,  
        FOREIGN KEY (bookId) REFERENCES books (id)
    )
    ''')
    
    # Update genres table to match the JSON structure
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS genres (
        id INTEGER PRIMARY KEY,
        genre TEXT NOT NULL,
        description TEXT,
        type TEXT,
        parentId INTEGER,
        createdAt TIMESTAMP,
        updatedAt TIMESTAMP,
        deletedAt TIMESTAMP
    )
    ''')
    
    # Create book_genres table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS book_genres (
        id INTEGER PRIMARY KEY,
        book_id INTEGER,
        genre_id INTEGER,
        rank INTEGER DEFAULT 0,
        importance REAL DEFAULT 0.0,
        FOREIGN KEY (book_id) REFERENCES books (id),
        FOREIGN KEY (genre_id) REFERENCES genres (id),
        UNIQUE(book_id, genre_id)
    )
    ''')
    
    # Create user_settings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_settings (
        id INTEGER PRIMARY KEY,
        key TEXT NOT NULL UNIQUE,
        value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        pubisher_description TEXT,
        business_email TEXT,
        business_phone TEXT,
        business_address TEXT,
        website TEXT,
        logoUrl TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Check and add local_file_path column to images table
    cursor.execute("PRAGMA table_info(images)")
    columns = cursor.fetchall()
    
    local_file_path_exists = any(col[1] == 'local_file_path' for col in columns)
    
    if not local_file_path_exists:
        cursor.execute("ALTER TABLE images ADD COLUMN local_file_path TEXT DEFAULT NULL")

