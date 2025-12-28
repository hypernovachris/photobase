import os
import sys
import unittest
from PIL import Image, ExifTags

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.image_processing import get_exif_string

class TestExif(unittest.TestCase):
    def setUp(self):
        self.test_dir = "tests/temp_images"
        os.makedirs(self.test_dir, exist_ok=True)
        self.exif_image_path = os.path.join(self.test_dir, "exif_test.jpg")
        self.no_exif_image_path = os.path.join(self.test_dir, "no_exif_test.jpg")
        
    def tearDown(self):
        # clean up
        if os.path.exists(self.exif_image_path):
            os.remove(self.exif_image_path)
        if os.path.exists(self.no_exif_image_path):
            os.remove(self.no_exif_image_path)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_get_exif_string_unavailable(self):
        # Create plain image
        img = Image.new('RGB', (100, 100), color='red')
        img.save(self.no_exif_image_path)
        
        result = get_exif_string(self.no_exif_image_path)
        self.assertEqual(result, "Unavailable")
        
    def test_get_exif_string_success(self):
        # Create image with EXIF
        img = Image.new('RGB', (100, 100), color='blue')
        
        # Construct EXIF data
        # IDs:
        # FocalLength: 37386
        # ISOSpeedRatings: 34855
        # ExposureTime: 33434
        # FNumber: 33437
        
        exif = img.getexif()
        exif[37386] = 35.0 # 35mm
        exif[34855] = 64 # ISO 64
        exif[33434] = 0.005 # 1/200 s
        exif[33437] = 1.4 # f/1.4
        
        img.save(self.exif_image_path, exif=exif)
        
        result = get_exif_string(self.exif_image_path)
        # Expected: "35mm, ISO 64, 1/200 s, f/1.4"
        self.assertEqual(result, "35mm, ISO 64, 1/200 s, f/1.4")

    def test_get_exif_string_missing_fields(self):
         # Create image with partial EXIF
        img = Image.new('RGB', (100, 100), color='green')
        exif = img.getexif()
        exif[37386] = 50.0 # 50mm
        # Missing others
        img.save(self.exif_image_path, exif=exif)
        
        result = get_exif_string(self.exif_image_path)
        self.assertEqual(result, "Unavailable")

if __name__ == '__main__':
    unittest.main()
