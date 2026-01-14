import os
import sqlite3
from .base_repository import BaseRepository

class ImageRepository(BaseRepository):
    def add_or_update_image(self, file_path, last_modified, thumbnail_path, camera=None, lens=None):
        self.cursor.execute("""
          INSERT INTO images (file_path, last_modified, thumbnail_path, camera, lens)
          VALUES (?, ?, ?, ?, ?)
          ON CONFLICT(file_path) DO UPDATE SET
            last_modified = excluded.last_modified,
            thumbnail_path = excluded.thumbnail_path,
            camera = COALESCE(excluded.camera, images.camera),
            lens = COALESCE(excluded.lens, images.lens)
        """, (file_path, last_modified, thumbnail_path, camera, lens))
        # Commit removed - handled by main helper or batched

    def get_all_images(self):
        # get all images from the database
        self.cursor.execute("SELECT * FROM images")
        return self.cursor.fetchall()

    def get_image_metadata(self, file_path):
        self.cursor.execute("SELECT camera, lens FROM images WHERE file_path = ?", (file_path,))
        return self.cursor.fetchone()
    
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
                        print(f"Failed to remove thumbnail: {thumb_path}")
                        pass

            # Delete database entries
            self.cursor.execute(f"DELETE FROM images WHERE file_path IN ({placeholders})", tuple(chunk))
            # TODO: should we also remove faces, tags?
            # and make sure to remove any orphaned tags/people
        
        self.connection.commit()

    def get_image_id(self, file_path):
        self.cursor.execute("SELECT id FROM images WHERE file_path = ?", (file_path,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    # --- Scanning & Status ---

    def get_unscanned_images(self, limit=None):
        if limit:
            self.cursor.execute("SELECT id, file_path FROM images WHERE scanned_for_faces = 0 LIMIT ?", (limit,))
        else:
            self.cursor.execute("SELECT id, file_path FROM images WHERE scanned_for_faces = 0")
        return self.cursor.fetchall()
        
    def claim_unscanned_images(self, limit=10):
        """
        Atomically gets a batch of unscanned images and marks them as in-progress (-1).
        Returns list of (id, file_path).
        """
        try:
            # We need an immediate transaction to prevent race conditions
            self.cursor.execute("BEGIN IMMEDIATE")
            
            self.cursor.execute("SELECT id, file_path FROM images WHERE scanned_for_faces = 0 LIMIT ?", (limit,))
            rows = self.cursor.fetchall()
            
            if rows:
                ids = [r[0] for r in rows]
                placeholders = ",".join("?" for _ in ids)
                self.cursor.execute(f"UPDATE images SET scanned_for_faces = -1 WHERE id IN ({placeholders})", tuple(ids))
                self.connection.commit()
            else:
                self.connection.rollback() # Nothing to do
                
            return rows
        except Exception as e:
            print(f"Error claiming batch: {e}")
            try:
                self.connection.rollback()
            except:
                pass
            return []
            
    def reset_stuck_scans(self):
        """Resets any scans marked as in-progress (-1) back to 0 on startup."""
        try:
            self.cursor.execute("UPDATE images SET scanned_for_faces = 0 WHERE scanned_for_faces = -1")
            self.connection.commit()
        except sqlite3.OperationalError:
            pass # Table might not exist yet

    def get_unscanned_count(self):
        try:
            self.cursor.execute("SELECT COUNT(*) FROM images WHERE scanned_for_faces = 0")
            return self.cursor.fetchone()[0]
        except sqlite3.OperationalError:
            return 0

    def mark_image_scanned(self, image_id):
        self.cursor.execute("UPDATE images SET scanned_for_faces = 1 WHERE id = ?", (image_id,))
        # Commit should be handled by caller usually, but for safety in long loops we might commit periodically.

    # --- Filtering ---

    def get_filtered_months(self, tag_id=None, person_id=None):
        """Returns a list of distinct month strings (YYYY-MM) based on filters."""
        if tag_id is not None:
            query = """
                SELECT DISTINCT strftime('%Y-%m', datetime(i.last_modified, 'unixepoch')) AS month 
                FROM images i
                JOIN image_tags it ON i.id = it.image_id
                WHERE it.tag_id = ?
                ORDER BY month DESC
            """
            self.cursor.execute(query, (tag_id,))
        elif person_id is not None:
            query = """
                SELECT DISTINCT strftime('%Y-%m', datetime(i.last_modified, 'unixepoch')) AS month 
                FROM images i
                JOIN faces f ON i.id = f.image_id
                WHERE f.person_id = ?
                ORDER BY month DESC
            """
            self.cursor.execute(query, (person_id,))
        else:
            query = """
                SELECT DISTINCT strftime('%Y-%m', datetime(last_modified, 'unixepoch')) AS month 
                FROM images 
                ORDER BY month DESC
            """
            self.cursor.execute(query)
        
        return [row[0] for row in self.cursor.fetchall()]

    def get_filtered_images(self, month_str, tag_id=None, person_id=None):
        """Returns a list of (file_path, thumbnail_path) tuples for a given month and filters."""
        if tag_id is not None:
            query = """
                SELECT i.file_path, i.thumbnail_path 
                FROM images i
                JOIN image_tags it ON i.id = it.image_id
                WHERE it.tag_id = ? 
                AND strftime('%Y-%m', datetime(i.last_modified, 'unixepoch')) = ?
                ORDER BY i.last_modified DESC
            """
            self.cursor.execute(query, (tag_id, month_str))
        elif person_id is not None:
            # Use DISTINCT on file_path to handle multiple faces of same person in one image
            query = """
                SELECT DISTINCT i.file_path, i.thumbnail_path 
                FROM images i
                JOIN faces f ON i.id = f.image_id
                WHERE f.person_id = ? 
                AND strftime('%Y-%m', datetime(i.last_modified, 'unixepoch')) = ?
                ORDER BY i.last_modified DESC
            """
            self.cursor.execute(query, (person_id, month_str))
        else:
            query = """
                SELECT file_path, thumbnail_path 
                FROM images
                WHERE strftime('%Y-%m', datetime(last_modified, 'unixepoch')) = ?
                ORDER BY last_modified DESC
            """
            self.cursor.execute(query, (month_str,))

        return self.cursor.fetchall()
