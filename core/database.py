import sqlite3
import os
from .repositories.image_repository import ImageRepository
from .repositories.tag_repository import TagRepository
from .repositories.person_repository import PersonRepository

class Database:
  def __init__(self, db_path="photos.db"):
    self.db_path = db_path
    self.connection = None
    self.cursor = None
    
    # Repositories
    self.images = None
    self.tags = None
    self.people = None

  def connect(self):
    self.connection = sqlite3.connect(self.db_path)
    self.cursor = self.connection.cursor()
    self.create_table_if_not_exists()
    
    # Initialize repositories with shared connection/cursor
    self.images = ImageRepository(self.connection, self.cursor)
    self.tags = TagRepository(self.connection, self.cursor)
    self.people = PersonRepository(self.connection, self.cursor)
  
    self.connection.commit()

  
  
  def create_table_if_not_exists(self):
    # Enable foreign keys
    self.cursor.execute("PRAGMA foreign_keys = ON;")
    
    self.cursor.execute("""
      CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT UNIQUE,
        last_modified INTEGER,
        thumbnail_path TEXT,
        scanned_for_faces INTEGER DEFAULT 0,
        camera TEXT,
        lens TEXT
      )
    """)

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
    
    # People and Faces
    self.cursor.execute("""
      CREATE TABLE IF NOT EXISTS people (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        uuid TEXT UNIQUE,
        cover_face_quality REAL DEFAULT 0
      )
    """)
    

    self.cursor.execute("""
      CREATE TABLE IF NOT EXISTS faces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_id INTEGER,
        person_id INTEGER,
        encoding BLOB,
        x INTEGER,
        y INTEGER,
        w INTEGER,
        h INTEGER,
        FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
        FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE CASCADE
      )
    """)

    self.connection.commit()
    # cleanup_orphan_tags is now in TagRepository, but we can't call it here 
    # freely unless we init repo first. 
    # For now, let's init repos in connect() AFTER table creation, which is what we do.
    # We can call it there if needed, or just let the repo handle it if called explicitly.
    # The original called it at the end of create_table...
    # We'll rely on the user/system calling it, or move it to connect().
  
  def close(self):
    if self.connection:
      self.connection.close()
  
  def commit(self):
    if self.connection:
      self.connection.commit()

db = Database()