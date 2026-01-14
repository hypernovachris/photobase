import uuid
from .base_repository import BaseRepository

class PersonRepository(BaseRepository):
    def create_person(self, name=None):
        new_uuid = str(uuid.uuid4())
        self.cursor.execute("INSERT INTO people (name, uuid) VALUES (?, ?)", (name, new_uuid))
        return self.cursor.lastrowid

    def get_person(self, person_id):
        self.cursor.execute("SELECT id, name FROM people WHERE id = ?", (person_id,))
        return self.cursor.fetchone()
        
    def get_person_uuid(self, person_id):
        self.cursor.execute("SELECT uuid FROM people WHERE id = ?", (person_id,))
        res = self.cursor.fetchone()
        return res[0] if res else None
    
    def get_person_score(self, person_id):
        self.cursor.execute("SELECT cover_face_quality FROM people WHERE id = ?", (person_id,))
        res = self.cursor.fetchone()
        return res[0] if res else 0.0

    def update_person_cover_score(self, person_id, score):
        self.cursor.execute("UPDATE people SET cover_face_quality = ? WHERE id = ?", (score, person_id))

    def add_face(self, image_id, person_id, encoding, rect):
        x, y, w, h = rect
        # Ensure encoding is bytes
        if not isinstance(encoding, bytes):
            encoding = encoding.tobytes()
            
        self.cursor.execute("""
            INSERT INTO faces (image_id, person_id, encoding, x, y, w, h)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (image_id, person_id, encoding, x, y, w, h))

    def clear_faces_for_image(self, image_id):
        self.cursor.execute("DELETE FROM faces WHERE image_id = ?", (image_id,))

    def get_all_people_with_counts(self):
        # Returns [(id, name, count, face_id, image_path, x, y, w, h, uuid), ...]
        query = """
          SELECT p.id, p.name, COUNT(f.id) as cnt,
                 (SELECT f2.id FROM faces f2 WHERE f2.person_id = p.id LIMIT 1) as face_id,
                 (
                     SELECT i.file_path 
                     FROM faces f3 
                     JOIN images i ON f3.image_id = i.id 
                     WHERE f3.person_id = p.id 
                     ORDER BY i.last_modified DESC 
                     LIMIT 1
                 ) as file_path,
                 (SELECT f4.x FROM faces f4 WHERE f4.person_id = p.id LIMIT 1) as fx,
                 (SELECT f4.y FROM faces f4 WHERE f4.person_id = p.id LIMIT 1) as fy,
                 (SELECT f4.w FROM faces f4 WHERE f4.person_id = p.id LIMIT 1) as fw,
                 (SELECT f4.h FROM faces f4 WHERE f4.person_id = p.id LIMIT 1) as fh,
                 p.uuid
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

    def get_faces_for_image(self, image_id):
        self.cursor.execute("""
            SELECT f.id, p.name, f.x, f.y, f.w, f.h, p.id
            FROM faces f
            LEFT JOIN people p ON f.person_id = p.id
            WHERE f.image_id = ?
        """, (image_id,))
        return self.cursor.fetchall()

    def remove_face(self, face_id):
        self.cursor.execute("DELETE FROM faces WHERE id = ?", (face_id,))

    def update_face_person_id(self, face_id, new_person_id):
        self.cursor.execute("UPDATE faces SET person_id = ? WHERE id = ?", (new_person_id, face_id))

    def remove_person_from_image(self, image_id, person_id):
        self.cursor.execute("UPDATE faces SET person_id = NULL WHERE image_id = ? AND person_id = ?", (image_id, person_id))
