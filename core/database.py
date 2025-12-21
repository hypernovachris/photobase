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
    if not file_paths:
        return
        
    # get thumbnail paths for entries we are about to remove
    # optimize: chunk the query if list is too large (SQLite limit is usually 999 vars)
    chunk_size = 900
    file_paths_list = list(file_paths)
    
    for i in range(0, len(file_paths_list), chunk_size):
        chunk = file_paths_list[i:i + chunk_size]
        placeholders = ",".join("?" for _ in chunk)
        
        self.cursor.execute(f"SELECT thumbnail_path FROM images WHERE file_path NOT IN ({placeholders})", tuple(chunk))
        paths_to_delete = self.cursor.fetchall()
        
        # remove them
        for path_to_delete in paths_to_delete:
            old_thumb_path = path_to_delete[0]
            if os.path.exists(old_thumb_path):
                try:
                    os.remove(old_thumb_path)
                except OSError:
                    pass

        # remove entries for files that no longer exist
        self.cursor.execute(f"DELETE FROM images WHERE file_path NOT IN ({placeholders})", tuple(chunk))
    
    self.connection.commit()

db = Database()