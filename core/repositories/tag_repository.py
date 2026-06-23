import sqlite3
from .base_repository import BaseRepository

class TagRepository(BaseRepository):

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

    def rename_tag(self, tag_id, new_name):
        new_name = new_name.strip()
        if not new_name:
            return False
        
        try:
            # check for existing
            self.cursor.execute("SELECT id FROM tags WHERE name = ?", (new_name,))
            if self.cursor.fetchone():
                return False
                
            self.cursor.execute("UPDATE tags SET name = ? WHERE id = ?", (new_name, tag_id))
            return True
        except sqlite3.Error:
            return False

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
        query = """
          SELECT 
              t.id,
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
          ORDER BY t.name
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def delete_tag(self, tag_id):
        try:
            self.cursor.execute("DELETE FROM image_tags WHERE tag_id = ?", (tag_id,))
            self.cursor.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
            return True
        except sqlite3.Error:
            return False
