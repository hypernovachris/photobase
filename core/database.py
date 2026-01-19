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
    
    self.cursor.execute("""
      CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT UNIQUE,
        last_modified INTEGER,
        date_taken INTEGER,
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
                self.connection.commit()
                print(f"Migrated {len(updates)} images.")
        except ImportError:
            print("Could not import get_date_taken for migration backfill.")
            pass



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

    self.connection.commit()

    # cleanup_orphan_tags is now in TagRepository, but we can't call it here 
    # freely unless we init repo first. 
    # For now, let's init repos in connect() AFTER table creation, which is what we do.
    # We can call it there if needed, or just let the repo handle it if called explicitly.
    # The original called it at the end of create_table...
    # We'll rely on the user/system calling it, or move it to connect().
    # TODO: wtf? figure out what to do

  def close(self):
    if self.connection:
      self.connection.close()
  
  def commit(self):
    if self.connection:
      self.connection.commit()

db = Database()