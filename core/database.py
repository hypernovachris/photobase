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
  
    self.connection.commit()

  def cleanup_orphan_tags(self):
    # Only needed if foreign keys were off previously and items were deleted.
    self.cursor.execute("DELETE FROM image_tags WHERE image_id NOT IN (SELECT id FROM images)")
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
        scanned_for_faces INTEGER DEFAULT 0
      )
    """)
    # Add column if it doesn't exist (migration for existing DBs)
    try:
        self.cursor.execute("ALTER TABLE images ADD COLUMN scanned_for_faces INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass # Column likely already exists

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
        name TEXT
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
    self.cleanup_orphan_tags()
  
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

  # --- Tagging System ---

  def get_image_id(self, file_path):
      self.cursor.execute("SELECT id FROM images WHERE file_path = ?", (file_path,))
      result = self.cursor.fetchone()
      return result[0] if result else None

  def get_or_create_tag(self, name):
      name = name.strip()
      if not name:
          return None
      try:
          self.cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (name,))
          self.cursor.execute("SELECT id FROM tags WHERE name = ?", (name,))
          return self.cursor.fetchone()[0]
      except sqlite3.Error:
          return None

  def add_tag_to_image(self, image_id, tag_id):
      try:
          self.cursor.execute("INSERT OR IGNORE INTO image_tags (image_id, tag_id) VALUES (?, ?)", (image_id, tag_id))
          return True
      except sqlite3.Error:
          return False

  def remove_tag_from_image(self, image_id, tag_id):
      self.cursor.execute("DELETE FROM image_tags WHERE image_id = ? AND tag_id = ?", (image_id, tag_id))

  def get_tags_for_image(self, image_id):
      self.cursor.execute("""
          SELECT t.id, t.name 
          FROM tags t
          JOIN image_tags it ON t.id = it.tag_id
          WHERE it.image_id = ?
          ORDER BY t.name
      """, (image_id,))
      return self.cursor.fetchall()

  def get_all_tags(self):
      self.cursor.execute("SELECT id, name FROM tags ORDER BY name")
      return self.cursor.fetchall()

  def get_tags_with_metadata(self):
      # Returns [(name, count, cover_path, cover_thumb_path), ...]
      # We want the *latest* image for each tag as the cover.
      # SQLite scalar subqueries or MAX logic.
      # Since we need path AND thumb_path from the SAME image (the one with MAX last_modified),
      # we can use a window function or a correlated subquery.
      
      # Using correlated subquery for simplicity in SQLite:
      # SELECT t.name, COUNT(it.image_id),
      #   (SELECT file_path FROM images i2 JOIN image_tags it2 ON i2.id = it2.image_id WHERE it2.tag_id = t.id ORDER BY i2.last_modified DESC LIMIT 1),
      #   (SELECT thumbnail_path FROM images i3 JOIN image_tags it3 ON i3.id = it3.image_id WHERE it3.tag_id = t.id ORDER BY i3.last_modified DESC LIMIT 1)
      # FROM tags t ...
      
      # Actually we can do it with one subquery if we select the whole row or just use a CTE.
      
      query = """
        SELECT 
            t.name, 
            COUNT(it.image_id) as cnt,
            (
                SELECT i.file_path 
                FROM images i 
                JOIN image_tags it2 ON i.id = it2.image_id 
                WHERE it2.tag_id = t.id 
                ORDER BY i.last_modified DESC 
                LIMIT 1
            ) as cover_path,
            (
                SELECT i.thumbnail_path 
                FROM images i 
                JOIN image_tags it3 ON i.id = it3.image_id 
                WHERE it3.tag_id = t.id 
                ORDER BY i.last_modified DESC 
                LIMIT 1
            ) as cover_thumb
        FROM tags t
        LEFT JOIN image_tags it ON t.id = it.tag_id
        GROUP BY t.id
        HAVING cnt > 0
        ORDER BY t.name
      """
      self.cursor.execute(query)
      return self.cursor.fetchall()


  def get_common_tags_for_images(self, image_ids):
      if not image_ids:
          return []
      
      # We need tags that are present for ALL image_ids
      placeholders = ",".join("?" for _ in image_ids)
      query = f"""
          SELECT t.id, t.name
          FROM tags t
          JOIN image_tags it ON t.id = it.tag_id
          WHERE it.image_id IN ({placeholders})
          GROUP BY t.id, t.name
          HAVING COUNT(DISTINCT it.image_id) = ?
          ORDER BY t.name
      """
      # Args: list of image IDs + total count of images
      args = list(image_ids)
      args.append(len(image_ids))
      
      self.cursor.execute(query, tuple(args))
      self.cursor.execute(query, tuple(args))
      return self.cursor.fetchall()

  # --- People & Faces ---

  def get_unscanned_images(self):
      self.cursor.execute("SELECT id, file_path FROM images WHERE scanned_for_faces = 0")
      return self.cursor.fetchall()

  def mark_image_scanned(self, image_id):
      self.cursor.execute("UPDATE images SET scanned_for_faces = 1 WHERE id = ?", (image_id,))
      # Commit should be handled by caller usually, but for safety in long loops we might commit periodically.

  def create_person(self, name=None):
      self.cursor.execute("INSERT INTO people (name) VALUES (?)", (name,))
      return self.cursor.lastrowid

  def get_person(self, person_id):
      self.cursor.execute("SELECT id, name FROM people WHERE id = ?", (person_id,))
      return self.cursor.fetchone()

  def add_face(self, image_id, person_id, encoding, rect):
      x, y, w, h = rect
      # Ensure encoding is bytes
      if not isinstance(encoding, bytes):
          encoding = encoding.tobytes()
          
      self.cursor.execute("""
          INSERT INTO faces (image_id, person_id, encoding, x, y, w, h)
          VALUES (?, ?, ?, ?, ?, ?, ?)
      """, (image_id, person_id, encoding, x, y, w, h))

  def get_all_people_with_counts(self):
      # Returns [(id, name, count, face_id, image_path, x, y, w, h), ...]
      # We need a cover face. Let's pick the first one or one from the latest image.
      query = """
        SELECT p.id, p.name, COUNT(f.id) as cnt,
               (SELECT f2.id FROM faces f2 WHERE f2.person_id = p.id LIMIT 1) as face_id,
               (SELECT i.file_path FROM faces f3 JOIN images i ON f3.image_id = i.id WHERE f3.person_id = p.id LIMIT 1) as file_path,
               (SELECT f4.x FROM faces f4 WHERE f4.person_id = p.id LIMIT 1) as fx,
               (SELECT f4.y FROM faces f4 WHERE f4.person_id = p.id LIMIT 1) as fy,
               (SELECT f4.w FROM faces f4 WHERE f4.person_id = p.id LIMIT 1) as fw,
               (SELECT f4.h FROM faces f4 WHERE f4.person_id = p.id LIMIT 1) as fh
        FROM people p
        JOIN faces f ON p.id = f.person_id
        GROUP BY p.id
        ORDER BY cnt DESC
      """
      self.cursor.execute(query)
      return self.cursor.fetchall()

  def update_person_name(self, person_id, name):
      self.cursor.execute("UPDATE people SET name = ? WHERE id = ?", (name, person_id))

  def get_all_face_encodings(self):
      # Helper to get all known faces to matching
      # Returns [(person_id, encoding), ...]
      self.cursor.execute("SELECT person_id, encoding FROM faces")
      return self.cursor.fetchall()


db = Database()