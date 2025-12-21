import sqlite3
import os

class Database:
  def __init__(self, db_path="photos.db"):
    self.db_path = db_path
    self.connection = None
    self.cursor = None

  def connect(self):
    self.connection = sqlite3.connect(self.db_path)
    self.cursor = self.connection.cursor()
    self.create_table_if_not_exists()
  
  def create_table_if_not_exists(self):
    self.cursor.execute("""
      CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT UNIQUE,
        last_modified INTEGER,
        thumbnail_path TEXT
      )
    """)
    self.connection.commit()
  
  def close(self):
    if self.connection:
      self.connection.close()

  def add_or_update_image(self, file_path, last_modified, thumbnail_path):
    self.cursor.execute("""
      INSERT INTO images (file_path, last_modified, thumbnail_path)
      VALUES (?, ?, ?)
      ON CONFLICT(file_path) DO UPDATE SET
        last_modified = excluded.last_modified,
        thumbnail_path = excluded.thumbnail_path
    """, (file_path, last_modified, thumbnail_path))
    # Commit removed for batching

  def commit(self):
    if self.connection:
      self.connection.commit()

  def get_all_images(self):
    # get all images from the database
    self.cursor.execute("SELECT * FROM images")
    return self.cursor.fetchall()
  
  def get_all_image_paths_and_dates(self):
    self.cursor.execute("SELECT file_path, last_modified FROM images")
    return {row[0]: row[1] for row in self.cursor.fetchall()}

  def remove_missing_files(self, file_paths):
    # if no files are provided (found_files is empty), it implies that all files were removed / no files found.
    # so we should remove all from DB.
    if not file_paths:
        self.cursor.execute("SELECT thumbnail_path FROM images")
        paths_to_delete = self.cursor.fetchall()
        for path_to_delete in paths_to_delete:
            old_thumb_path = path_to_delete[0]
            if os.path.exists(old_thumb_path):
                try:
                    os.remove(old_thumb_path)
                except OSError:
                    pass
        self.cursor.execute("DELETE FROM images")
        self.connection.commit()
        return

    # To avoid deleting everything when chunking 'NOT IN', we must first find what to delete.
    # Get all current file paths from DB.
    self.cursor.execute("SELECT file_path FROM images")
    db_paths = set(row[0] for row in self.cursor.fetchall())
    
    # Identify orphans
    paths_to_remove = list(db_paths - set(file_paths))
    
    if not paths_to_remove:
        return

    # Delete orphans in chunks
    chunk_size = 900
    for i in range(0, len(paths_to_remove), chunk_size):
        chunk = paths_to_remove[i:i + chunk_size]
        placeholders = ",".join("?" for _ in chunk)
        
        # Get thumbnails to delete
        self.cursor.execute(f"SELECT thumbnail_path FROM images WHERE file_path IN ({placeholders})", tuple(chunk))
        thumbs_to_delete = self.cursor.fetchall()
        
        for (thumb_path,) in thumbs_to_delete:
            if os.path.exists(thumb_path):
                try:
                    os.remove(thumb_path)
                except OSError:
                    pass

        # Delete database entries
        self.cursor.execute(f"DELETE FROM images WHERE file_path IN ({placeholders})", tuple(chunk))
    
    self.connection.commit()

db = Database()