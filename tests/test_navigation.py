import unittest
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
import sys
import os

# Ensure QApp exists
app = QApplication.instance() or QApplication(sys.argv)

from core.gallery_model import GalleryModel

class TestGalleryNavigation(unittest.TestCase):
    def setUp(self):
        # Mock database to avoid real connection errors during init
        with patch('core.gallery_model.db'):
             self.model = GalleryModel()
        
        # Manually populate _sections for testing
        # Sections: Month -> Images
        self.model._sections = [
            {
                'month_text': 'Month 1',
                'images': [
                    {'path': 'path/to/img1.jpg', 'thumbnail': '...'},
                    {'path': 'path/to/img2.jpg', 'thumbnail': '...'},
                    {'path': 'path/to/img3.jpg', 'thumbnail': '...'},
                ]
            },
            {
                'month_text': 'Month 2',
                'images': [
                    {'path': 'path/to/img4.jpg', 'thumbnail': '...'},
                    {'path': 'path/to/img5.jpg', 'thumbnail': '...'},
                ]
            }
        ]
        self.paths = [
            'path/to/img1.jpg', 'path/to/img2.jpg', 'path/to/img3.jpg',
            'path/to/img4.jpg', 'path/to/img5.jpg'
        ]

    def test_next_within_section(self):
        # 1 -> 2
        next_path = self.model.get_next_image_path(self.paths[0])
        self.assertEqual(next_path, self.paths[1])
        # 2 -> 3
        next_path = self.model.get_next_image_path(self.paths[1])
        self.assertEqual(next_path, self.paths[2])

    def test_next_cross_section(self):
        # 3 (End of S1) -> 4 (Start of S2)
        next_path = self.model.get_next_image_path(self.paths[2])
        self.assertEqual(next_path, self.paths[3])

    def test_next_end_of_list(self):
        # 5 (End of list) -> None/Empty
        next_path = self.model.get_next_image_path(self.paths[4])
        self.assertEqual(next_path, "")

    def test_prev_within_section(self):
        # 2 -> 1
        prev_path = self.model.get_previous_image_path(self.paths[1])
        self.assertEqual(prev_path, self.paths[0])

    def test_prev_cross_section(self):
        # 4 (Start of S2) -> 3 (End of S1)
        prev_path = self.model.get_previous_image_path(self.paths[3])
        self.assertEqual(prev_path, self.paths[2])

    def test_prev_start_of_list(self):
        # 1 -> None/Empty
        prev_path = self.model.get_previous_image_path(self.paths[0])
        self.assertEqual(prev_path, "")

    def test_unknown_path(self):
        prev_path = self.model.get_previous_image_path("invalid/path")
        self.assertEqual(prev_path, "")
        next_path = self.model.get_next_image_path("invalid/path")
        self.assertEqual(next_path, "")

if __name__ == '__main__':
        unittest.main()
