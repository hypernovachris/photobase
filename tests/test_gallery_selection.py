import unittest
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
import sys
import os

# Ensure QApp exists
app = QApplication.instance() or QApplication(sys.argv)

from core.gallery_model import GalleryModel

class TestGallerySelection(unittest.TestCase):
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

    def test_single_click(self):
        # Click img1
        self.model.handle_selection(self.paths[0], Qt.KeyboardModifier.NoModifier.value)
        self.assertEqual(self.model.get_selected_paths(), [self.paths[0]])
        
        # Click img2 (replace)
        self.model.handle_selection(self.paths[1], Qt.KeyboardModifier.NoModifier.value)
        self.assertEqual(self.model.get_selected_paths(), [self.paths[1]])

    def test_ctrl_click(self):
        # Click img1
        self.model.handle_selection(self.paths[0], Qt.KeyboardModifier.NoModifier.value)
        
        # Ctrl+Click img2 (add)
        self.model.handle_selection(self.paths[1], Qt.KeyboardModifier.ControlModifier.value)
        selected = self.model.get_selected_paths()
        self.assertEqual(len(selected), 2)
        self.assertIn(self.paths[0], selected)
        self.assertIn(self.paths[1], selected)
        
        # Ctrl+Click img1 (toggle off)
        self.model.handle_selection(self.paths[0], Qt.KeyboardModifier.ControlModifier.value)
        self.assertEqual(self.model.get_selected_paths(), [self.paths[1]])

    def test_shift_click_range_same_section(self):
        # Click img1
        self.model.handle_selection(self.paths[0], Qt.KeyboardModifier.NoModifier.value)
        
        # Shift+Click img3 (1..3)
        self.model.handle_selection(self.paths[2], Qt.KeyboardModifier.ShiftModifier.value)
        selected = self.model.get_selected_paths()
        self.assertEqual(len(selected), 3)
        self.assertIn(self.paths[0], selected)
        self.assertIn(self.paths[1], selected)
        self.assertIn(self.paths[2], selected)

    def test_shift_click_range_cross_section(self):
        # Click img2
        self.model.handle_selection(self.paths[1], Qt.KeyboardModifier.NoModifier.value)
        
        # Shift+Click img4 (2..4 -> img2, img3, img4)
        self.model.handle_selection(self.paths[3], Qt.KeyboardModifier.ShiftModifier.value)
        selected = self.model.get_selected_paths()
        self.assertEqual(len(selected), 3)
        self.assertIn(self.paths[1], selected)
        self.assertIn(self.paths[2], selected)
        self.assertIn(self.paths[3], selected)

    def test_shift_click_reverse(self):
        # Click img4
        self.model.handle_selection(self.paths[3], Qt.KeyboardModifier.NoModifier.value)
        
        # Shift+Click img2 (4..2 -> 2, 3, 4)
        self.model.handle_selection(self.paths[1], Qt.KeyboardModifier.ShiftModifier.value)
        selected = self.model.get_selected_paths()
        self.assertEqual(len(selected), 3)
        self.assertIn(self.paths[1], selected)
        self.assertIn(self.paths[2], selected)
        self.assertIn(self.paths[3], selected)

if __name__ == '__main__':
        unittest.main()
