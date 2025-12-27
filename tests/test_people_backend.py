
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
# (top, right, bottom, left)
mock_fr.face_locations.return_value = [(10, 50, 60, 20)] # One face per image
# 128-d encoding
mock_fr.face_encodings.return_value = [b'\x01'*128] # Dummy encoding
mock_fr.face_encodings.return_value = [b'\x01'*128] # Dummy encoding
mock_fr.compare_faces.side_effect = lambda known, unknown, tolerance=0.6: [True] * len(known) if known else []


sys.modules['face_recognition'] = mock_fr
import core.face_scanner
from core.face_scanner import FaceScanner


class TestPeopleBackend(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_env"
        os.makedirs(self.test_dir, exist_ok=True)
        self.db_path = os.path.join(self.test_dir, "test_photos.db")
        self.db = Database(self.db_path)
        self.db.connect()
        
        # Add dummy image
        self.image_path = os.path.join(self.test_dir, "test.jpg")
        with open(self.image_path, "wb") as f:
            f.write(b"dummy image content")
            
        self.db.add_or_update_image(self.image_path, 123456, "thumb.jpg")
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
        unscanned = self.db.get_unscanned_images()

        self.assertEqual(len(unscanned), 1)
        
        # 2. Run Scanner
        scanner = core.face_scanner.FaceScanner()
        
        # We need to run the event loop to let thread work.
        # But for unit test, we can just instantiate Worker directly and run run() to test logic synchronously.
        # Testing full thread is harder.
        
        worker = core.face_scanner.FaceScannerWorker(scanner.signals)
        
        # Override DB path in worker (since it uses global 'db' import which points to 'photos.db')
        # Wait, the worker imports 'db' from core.database.
        # That global 'db' instance usually points to "photos.db".
        # We need to redirect it.
        core.face_scanner.db = self.db 
        
        worker.run()
        
        # Reconnect DB because worker closed it
        self.db.connect()

        
        # 3. Check Results
        # Image should be scanned
        self.db.cursor.execute("SELECT scanned_for_faces FROM images WHERE file_path = ?", (self.image_path,))
        scanned = self.db.cursor.fetchone()[0]
        self.assertEqual(scanned, 1)
        
        # Should have 1 person
        people = self.db.get_all_people_with_counts()
        self.assertEqual(len(people), 1)
        
        # Should have 1 face
        self.db.cursor.execute("SELECT count(*) FROM faces")
        count = self.db.cursor.fetchone()[0]
        self.assertEqual(count, 1)
        
        print("Backend Scan Verified.")

if __name__ == '__main__':
    unittest.main()
