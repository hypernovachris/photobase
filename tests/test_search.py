import unittest
import sqlite3
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.repositories.image_repository import ImageRepository

class TestSearchQueryBuilder(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.cursor = self.conn.cursor()
        self.repo = ImageRepository(self.conn, self.cursor)
        
    def tearDown(self):
        self.conn.close()
        
    def test_tag_filter(self):
        filters = [{'type': 'tag', 'value': 'Holiday'}]
        sql, params = self.repo._build_filter_conditions(filters)
        self.assertIn("image_tags", sql)
        self.assertIn("tags.name = ?", sql)
        self.assertEqual(params, ['Holiday'])

    def test_negated_tag_filter(self):
        filters = [{'type': 'tag', 'value': 'Holiday', 'negated': True}]
        sql, params = self.repo._build_filter_conditions(filters)
        self.assertIn("NOT IN", sql)
        self.assertEqual(params, ['Holiday'])

    def test_complex_and(self):
        filters = [
            {'type': 'tag', 'value': 'A'},
            {'type': 'tag', 'value': 'B'}
        ]
        sql, params = self.repo._build_filter_conditions(filters)
        self.assertIn(" AND ", sql)
        self.assertEqual(sql.count("IN (SELECT"), 2)
        self.assertEqual(params, ['A', 'B'])

    def test_date_before(self):
        filters = [{'type': 'before', 'value': '2023-01-01'}]
        sql, params = self.repo._build_filter_conditions(filters)
        self.assertIn("last_modified < ?", sql)
        self.assertIsInstance(params[0], float)

    def test_filename_filter(self):
        filters = [{'type': 'filename', 'value': 'IMG'}]
        sql, params = self.repo._build_filter_conditions(filters)
        self.assertIn("file_path LIKE ?", sql)
        self.assertIn("%\\IMG%", params[0]) 

if __name__ == '__main__':
    unittest.main()
