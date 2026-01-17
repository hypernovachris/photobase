
import unittest
import os
import shutil
import sqlite3
from core.database import Database
from PyQt6.QtCore import QCoreApplication
import sys
import time
from unittest.mock import MagicMock

# Mock face_recognition module
mock_fr = MagicMock()
mock_fr.load_image_file.return_value = "dummy_image_data"

# RETURN TWO IDENTICAL FACES
# Locations: Face 1 and Face 2 (Large enough to pass >150px filter)
mock_fr.face_locations.return_value = [
    (10, 200, 200, 10),   # Face 1: Height 190, Width 190
    (10, 400, 200, 210)   # Face 2: Height 190, Width 190
]

# Encodings: Two identical encodings
mock_fr.face_encodings.return_value = [
    b'\x01'*128, 
    b'\x01'*128
] 

# Landmarks
mock_fr.face_landmarks.return_value = [
    {'left_eye': [(10,10)], 'right_eye': [(20,10)], 'nose_bridge': [(15,15)]},
    {'left_eye': [(110,10)], 'right_eye': [(120,10)], 'nose_bridge': [(115,15)]}
]

# compare_faces logic:
# When checking the second face, known_encodings will contain the first face.
# We want it to match.
def side_effect_compare(known_encodings, face_encoding_to_check, tolerance=0.6):
    # If known_encodings is not empty, and the check encoding is our dummy, return True
    if len(known_encodings) > 0:
        return [True] * len(known_encodings) 
    return []

mock_fr.compare_faces.side_effect = side_effect_compare
import numpy as np
mock_fr.face_distance.return_value = np.array([0.0]) # Perfect match

sys.modules['face_recognition'] = mock_fr

import core.face_scanner
from core.face_scanner import FaceScannerWorker

class TestDuplicateFaces(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_env_dup"
        os.makedirs(self.test_dir, exist_ok=True)
        self.db_path = os.path.join(self.test_dir, "test_photos.db")
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except:
                pass
        self.db = Database(self.db_path)
        self.db.connect()
        
        # Add dummy image
        self.image_path = os.path.join(self.test_dir, "test.jpg")
        from PIL import Image
        img = Image.new('RGB', (500, 500), color = 'red')
        img.save(self.image_path)
            
        self.db.images.add_or_update_image(self.image_path, 123456, "thumb.jpg")
        self.db.commit()
        
        # Qt App needed for Signals
        if not QCoreApplication.instance():
            self.app = QCoreApplication(sys.argv)
        else:
            self.app = QCoreApplication.instance()

    def tearDown(self):
        if self.db:
            self.db.close()
        try:
            shutil.rmtree(self.test_dir)
        except:
            pass

    def test_duplicate_face_handling(self):
        # Close main thread DB to avoid locking
        self.db.close()

        # Patch Database to use our test DB
        with unittest.mock.patch('core.face_scanner.Database', side_effect=lambda: Database(self.db_path)):
            # Create worker directly to run synchronously-ish
            # We can't run .run() because it loops forever.
            # We will refactor a bit or just run it in a thread and stop it.
            
            # Re-create signals since app might need them
            scanner_signals = core.face_scanner.ScannerSignals()
            worker = FaceScannerWorker(scanner_signals, 0)
            
            import threading
            t = threading.Thread(target=worker.run)
            t.daemon = True
            t.start()
            
            # Wait for scan
            # We need to peek into the DB, so we need a connection
            verify_db = Database(self.db_path)
            verify_db.connect()

            start = time.time()
            done = False
            while time.time() - start < 5:
                # Check DB directly
                try:
                    verify_db.cursor.execute("SELECT scanned_for_faces FROM images WHERE file_path = ?", (self.image_path,))
                    row = verify_db.cursor.fetchone()
                    if row and row[0] == 1:
                        done = True
                        break
                except:
                    pass
                time.sleep(0.1)
                
            worker.stop()
            t.join(1)
            
            if not done:
                self.fail("Scanner timed out")
                
            # VERIFICATION
            
            # 1. How many people created? Should be 1.
            verify_db.cursor.execute("SELECT COUNT(*) FROM people")
            num_people = verify_db.cursor.fetchone()[0]
            print(f"Number of people created: {num_people}")
            self.assertEqual(num_people, 1, "Should create exactly 1 person for identical faces in same image")
            
            # 2. How many faces added? Should be 1 (since we skip the duplicate).
            verify_db.cursor.execute("SELECT COUNT(*) FROM faces")
            num_faces = verify_db.cursor.fetchone()[0]
            print(f"Number of faces added: {num_faces}")
            self.assertEqual(num_faces, 1, "Should add exactly 1 face (skipping the duplicate)")
            
            verify_db.close()

if __name__ == '__main__':
    unittest.main()
