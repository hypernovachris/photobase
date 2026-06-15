import os
import sqlite3
from .base_repository import BaseRepository

class ImageRepository(BaseRepository):
    def add_or_update_image(self, file_path, last_modified, thumbnail_path, camera=None, lens=None, date_taken=None):
        self.cursor.execute("""
          INSERT INTO images (file_path, last_modified, thumbnail_path, camera, lens, date_taken)
          VALUES (?, ?, ?, ?, ?, ?)
          ON CONFLICT(file_path) DO UPDATE SET
            last_modified = excluded.last_modified,
            date_taken = excluded.date_taken,
            thumbnail_path = excluded.thumbnail_path,
            camera = COALESCE(excluded.camera, images.camera),
            lens = COALESCE(excluded.lens, images.lens)
        """, (file_path, last_modified, thumbnail_path, camera, lens, date_taken))
        # Commit removed - handled by main helper or batched

    def update_image_path(self, old_path, new_path, new_thumb_path):
        self.cursor.execute("UPDATE images SET file_path = ?, thumbnail_path = ? WHERE file_path = ?", (new_path, new_thumb_path, old_path))
    def get_all_images(self):
        # get all images from the database
        self.cursor.execute("SELECT * FROM images")
        return self.cursor.fetchall()

    def get_image_metadata(self, file_path):
        self.cursor.execute("SELECT camera, lens, date_taken FROM images WHERE file_path = ?", (file_path,))
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
            # TODO: should we also remove tags?
            # YES WE ABSOLUTELY MUST, make sure to remove any orphaned tags
            # Make sure we're already doing this
        
        self.connection.commit()

    def get_image_id(self, file_path):
        self.cursor.execute("SELECT id FROM images WHERE file_path = ?", (file_path,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    # --- Filtering ---

    def _parse_date(self, date_str):
        from datetime import datetime
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.timestamp()
        except ValueError:
            return 0

    def get_all_cameras(self):
        query = "SELECT DISTINCT camera FROM images WHERE camera IS NOT NULL AND camera != '' ORDER BY camera"
        self.cursor.execute(query)
        return [row[0] for row in self.cursor.fetchall()]

    def get_all_lenses(self):
        query = "SELECT DISTINCT lens FROM images WHERE lens IS NOT NULL AND lens != '' ORDER BY lens"
        self.cursor.execute(query)
        return [row[0] for row in self.cursor.fetchall()]

    def _build_filter_conditions(self, filters):
        conditions = []
        params = []
        
        if not filters:
            return "", []

        for f in filters:
            ftype = f.get('type')
            val = f.get('value')
            negated = f.get('negated', False)
            
            # Helper for subquery existence
            def add_subquery_condition(sub_sql, sub_params):
                op = "NOT IN" if negated else "IN"
                conditions.append(f"id {op} ({sub_sql})")
                params.extend(sub_params)

            if ftype == 'tag':
                # val is tag name
                add_subquery_condition(
                    "SELECT image_id FROM image_tags JOIN tags ON image_tags.tag_id = tags.id WHERE tags.name = ?",
                    [val]
                )
            elif ftype == 'camera':
                # Handle NULLs for negation
                if negated:
                    conditions.append("(camera NOT LIKE ? OR camera IS NULL)")
                else:
                    conditions.append("camera LIKE ?")
                params.append(f"%{val}%")
            elif ftype == 'lens':
                 # Handle NULLs for negation
                if negated:
                    conditions.append("(lens NOT LIKE ? OR lens IS NULL)")
                else:
                    conditions.append("lens LIKE ?")
                params.append(f"%{val}%")
            elif ftype == 'folder':
                ops = "NOT LIKE" if negated else "LIKE"
                logic_op = "AND" if negated else "OR"
                
                sub_conds = []
                sub_params = []
                
                # Slash
                sub_conds.append(f"file_path {ops} ?")
                sub_params.append(f"%/{val}/%")
                
                # Backslash
                sub_conds.append(f"file_path {ops} ?")
                sub_params.append(f"%\\{val}\\%")
                
                # Correct join logic
                combined = f"({' ' + logic_op + ' '.join(sub_conds)})" 
                # Wait, ' '.join(sub_conds) joins them with spaces. 
                # We want to join them with the operator.
                # " OR ".join(sub_conds)
                
                combined = f"({(' ' + logic_op + ' ').join(sub_conds)})"
                conditions.append(combined)
                params.extend(sub_params)
                
            elif ftype == 'extension':
                op = "NOT LIKE" if negated else "LIKE"
                conditions.append(f"file_path {op} ?")
                # e.g. .jpg
                if not val.startswith('.'):
                    val = '.' + val
                params.append(f"%{val}")
            elif ftype == 'filename':
                ops = "NOT LIKE" if negated else "LIKE"
                logic_op = "AND" if negated else "OR"
                
                sub_conds = []
                sub_params = []
                
                # Starts with val after /
                sub_conds.append(f"file_path {ops} ?")
                sub_params.append(f"%/{val}%")
                
                # Starts with val after \
                sub_conds.append(f"file_path {ops} ?")
                sub_params.append(f"%\\{val}%")
                 
                combined = f"({(' ' + logic_op + ' ').join(sub_conds)})"
                conditions.append(combined)
                params.extend(sub_params)

            elif ftype == 'before':
                ts = self._parse_date(val)
                op = ">=" if negated else "<"
                conditions.append(f"date_taken {op} ?")
                params.append(ts)
            elif ftype == 'since':
                ts = self._parse_date(val)
                op = "<" if negated else ">" # Since means >=
                conditions.append(f"date_taken {op} ?")
                params.append(ts)
            elif ftype == 'date_between':
                pass
            
            if ftype == 'between' or ftype == 'date_between':
                # val is JSON string now?
                import json
                try:
                    if isinstance(val, str):
                        val_obj = json.loads(val)
                    else:
                        val_obj = val
                except:
                    val_obj = {}
                    
                start_ts = self._parse_date(val_obj.get('start', ''))
                end_ts = self._parse_date(val_obj.get('end', ''))
                end_ts += 86400 
                
                if negated:
                    conditions.append("(date_taken < ? OR date_taken > ?)")
                    params.extend([start_ts, end_ts])
                else:
                    conditions.append("date_taken BETWEEN ? AND ?")
                    params.extend([start_ts, end_ts])

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
            
        return where_clause, params

    def get_filtered_months(self, filters=None):
        """
        Returns a list of distinct month strings (YYYY-MM) based on filters.
        filters: List of dicts {type, value, negated}
        """
        if filters is None: filters = []
        
        where_clause, params = self._build_filter_conditions(filters)
        
        query = f"""
            SELECT DISTINCT strftime('%Y-%m', datetime(date_taken, 'unixepoch')) AS month 
            FROM images 
            {where_clause}
            ORDER BY month DESC
        """
        self.cursor.execute(query, params)
        return [row[0] for row in self.cursor.fetchall()]

    def get_filtered_images(self, month_str, filters=None):
        """
        Returns a list of (file_path, thumbnail_path) tuples for a given month and filters.
        """
        if filters is None: filters = []
        
        where_clause, params = self._build_filter_conditions(filters)
        
        # We need to add the month condition to the WHERE clause using AND
        # If where_clause is empty, start with WHERE. Else append AND.
        
        month_condition = "strftime('%Y-%m', datetime(date_taken, 'unixepoch')) = ?"
        
        if where_clause:
            final_where = f"{where_clause} AND {month_condition}"
        else:
            final_where = f"WHERE {month_condition}"
            
        params.append(month_str)
        
        query = f"""
            SELECT file_path, thumbnail_path 
            FROM images
            {final_where}
            ORDER BY date_taken DESC
        """
        self.cursor.execute(query, params)

        return self.cursor.fetchall()
    def get_filtered_images_with_month(self, filters=None):
        """
        Returns a list of (file_path, thumbnail_path, month_str) tuples, ordered by date descending.
        """
        if filters is None: filters = []
        
        where_clause, params = self._build_filter_conditions(filters)
        
        # We select the month string as well to group by it in the application
        query = f"""
            SELECT file_path, thumbnail_path, strftime('%Y-%m', datetime(date_taken, 'unixepoch')) AS month
            FROM images 
            {where_clause}
            ORDER BY date_taken DESC
        """
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
