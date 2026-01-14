
import unittest
import os
import shutil
import sqlite3
from core.database import Database
from PyQt6.QtCore import QCoreApplication
import sys
import time

# Mock face_recognition to avoid needing models valid for the test if environment is strict,
# OR use real one if available.
# requirements.txt has it, so assume it works.
# But for stability, if no faces found in the random image, tests might fail.
# The user uploaded image looks like a sketch. Face recognition might NOT work on sketches.
# The sketch has stick figures.
# face_recognition works on real photos.
# I should MOCK face_recognition for this test to be deterministic.

from unittest.mock import MagicMock
import sys


# Mocking face_recognition module
mock_fr = MagicMock()
mock_fr.load_image_file.return_value = "dummy_image_data"
# (top, right, bottom, left). Height = 200-10 = 190 > 150.
mock_fr.face_locations.return_value = [(10, 200, 200, 10)] # One face per image
# 128-d encoding
mock_fr.face_encodings.return_value = [b'\x01'*128] # Dummy encoding
mock_fr.face_landmarks.return_value = [{
    'left_eye': [(10,10)], 
    'right_eye': [(20,10)], 
    'nose_bridge': [(15,15)]
}]
mock_fr.compare_faces.side_effect = lambda known, unknown, tolerance=0.6: [True] * len(known) if known else []


sys.modules['face_recognition'] = mock_fr
import core.face_scanner
from core.face_scanner import FaceScanner


class TestPeopleBackend(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_env"
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
        img = Image.new('RGB', (100, 100), color = 'red')
        img.save(self.image_path)
            
        self.db.images.add_or_update_image(self.image_path, 123456, "thumb.jpg")
        # Force reset scanned state in case DB persisted
        self.db.cursor.execute("UPDATE images SET scanned_for_faces = 0")
        self.db.commit()

        # Qt App needed for Signals
        if not QCoreApplication.instance():
            self.app = QCoreApplication(sys.argv)
        else:
            self.app = QCoreApplication.instance()

    def tearDown(self):
        self.db.close()
        try:
            shutil.rmtree(self.test_dir)
        except:
            pass

    def test_scanning_flow(self):
        # 1. Check Initial State
        self.db.cursor.execute("SELECT * FROM images")
        print("DEBUG IMAGES:", self.db.cursor.fetchall())
        unscanned = self.db.images.get_unscanned_images()

        self.assertEqual(len(unscanned), 1)
        
        # 2. Run Scanner
        import threading
        
        # Patch Database in core.face_scanner to use test DB path
        with unittest.mock.patch('core.face_scanner.Database', side_effect=lambda: Database(self.db_path)):
            scanner = core.face_scanner.FaceScanner()
            worker = core.face_scanner.FaceScannerWorker(scanner.signals, 0)
            
            t = threading.Thread(target=worker.run)
            t.daemon = True
            t.start()
            
            # Wait for completion
            timeout = 5
            start = time.time()
            done = False
            while time.time() - start < timeout:
                # Check directly in DB if scanned
                self.db.cursor.execute("SELECT scanned_for_faces FROM images WHERE file_path = ?", (self.image_path,))
                res = self.db.cursor.fetchone()
                if res and res[0] == 1:
                    done = True
                    break
                time.sleep(0.1)
                
            worker.stop()
            # Give it a moment to stop
            t.join(timeout=1)

            if not done:
                self.fail("Timeout waiting for scanner")
        
        # 3. Check Results
        # Image should be scanned
        self.db.cursor.execute("SELECT scanned_for_faces FROM images WHERE file_path = ?", (self.image_path,))
        scanned = self.db.cursor.fetchone()[0]
        self.assertEqual(scanned, 1)
        
        # Should have 1 person
        people = self.db.people.get_all_people_with_counts()
        self.assertEqual(len(people), 1)
        
        # Should have 1 face
        self.db.cursor.execute("SELECT count(*) FROM faces")
        count = self.db.cursor.fetchone()[0]
        self.assertEqual(count, 1)
        
        print("Backend Scan Verified.")

if __name__ == '__main__':
    unittest.main()
