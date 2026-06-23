import sqlite3
import os
from .repositories.image_repository import ImageRepository
from .repositories.tag_repository import TagRepository

class Database:
  def __init__(self, db_path="photos.db"):
    self.db_path = db_path
    self.connection = None
    self.cursor = None
    
    # Repositories
    self.images = None
    self.tags = None

  def connect(self):
    self.connection = sqlite3.connect(self.db_path)
    self.cursor = self.connection.cursor()
    self.create_table_if_not_exists()
    
    # Initialize repositories with shared connection/cursor
    self.images = ImageRepository(self.connection, self.cursor)
    self.tags = TagRepository(self.connection, self.cursor)
  
    self.connection.commit()

  
  
  def create_table_if_not_exists(self):
    # Enable foreign keys
    self.cursor.execute("PRAGMA foreign_keys = ON;")
    self.cursor.execute("PRAGMA journal_mode = WAL;")
    self.cursor.execute("PRAGMA synchronous = NORMAL;")
    
    self.cursor.execute("""
      CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT UNIQUE,
        last_modified INTEGER,
        date_taken INTEGER,
        month_str TEXT,
        thumbnail_path TEXT,
        scanned_for_faces INTEGER DEFAULT 0,
        camera TEXT,
        lens TEXT
      )
    """)
    
    # Schema Migration: Add date_taken if it doesn't exist
    try:
        self.cursor.execute("SELECT date_taken FROM images LIMIT 1")
    except sqlite3.OperationalError:
        print("Migrating database: Adding date_taken column...")
        self.cursor.execute("ALTER TABLE images ADD COLUMN date_taken INTEGER")
        
        # Backfill existing images
        print("Migrating database: Backfilling date_taken for existing images...")
        self.cursor.execute("SELECT id, file_path, last_modified FROM images")
        rows = self.cursor.fetchall()
        
        # Import locally to avoid circular dependency (image_processing imports db)
        try:
            from core.image_processing import get_date_taken
            
            updates = []
            for row in rows:
                img_id, file_path, last_modified = row
                
                # Try to get from EXIF
                dt = get_date_taken(file_path)
                
                # Fallback to last_modified
                if dt is None:
                    dt = last_modified
                
                updates.append((dt, img_id))
                
            if updates:
                self.cursor.executemany("UPDATE images SET date_taken = ? WHERE id = ?", updates)
            print(f"Migrated {len(updates)} images.")
        except ImportError:
            print("Could not import get_date_taken for migration backfill.")
            pass

    # Schema Migration: Add month_str if it doesn't exist
    try:
        self.cursor.execute("SELECT month_str FROM images LIMIT 1")
    except sqlite3.OperationalError:
        print("Migrating database: Adding month_str column...")
        self.cursor.execute("ALTER TABLE images ADD COLUMN month_str TEXT")
        
        # Backfill existing images
        print("Migrating database: Backfilling month_str for existing images...")
        self.cursor.execute("SELECT id, date_taken, last_modified FROM images")
        rows = self.cursor.fetchall()
        
        import datetime
        updates = []
        for row in rows:
            img_id, date_taken, last_modified = row
            dt_val = date_taken if date_taken is not None else last_modified
            try:
                dt = datetime.datetime.fromtimestamp(dt_val)
                m_str = dt.strftime("%Y-%m")
            except (ValueError, OSError, OverflowError, TypeError):
                m_str = "Unknown"
            updates.append((m_str, img_id))
            
        if updates:
            self.cursor.executemany("UPDATE images SET month_str = ? WHERE id = ?", updates)
            self.connection.commit()
            print(f"Migrated {len(updates)} images with month_str.")

    # Indices for performance
    self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_date_taken ON images(date_taken DESC)")
    self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_month_str ON images(month_str)")
    self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_image_tags_tag_id ON image_tags(tag_id)")

    # Tagging support
    self.cursor.execute("""
      CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
      )
    """)
    self.cursor.execute("""
      CREATE TABLE IF NOT EXISTS image_tags (
        image_id INTEGER,
        tag_id INTEGER,
        PRIMARY KEY (image_id, tag_id),
        FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
      )
    """)

    # Automatic trigger to clean up orphaned tags when relations are removed
    self.cursor.execute("""
      CREATE TRIGGER IF NOT EXISTS cleanup_tags_after_image_tag_delete
      AFTER DELETE ON image_tags
      BEGIN
          DELETE FROM tags
          WHERE id = OLD.tag_id
            AND NOT EXISTS (SELECT 1 FROM image_tags WHERE tag_id = OLD.tag_id);
      END;
    """)

    self.connection.commit()

  def close(self):
    if self.connection:
      self.connection.close()
  
  def commit(self):
    if self.connection:
      self.connection.commit()

db = Database()