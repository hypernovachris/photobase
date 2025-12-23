import sys
import os

import sqlite3

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import Database

def test_tagging_backend():
    # Setup temporary DB
    db_path = "test_tags.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db = Database(db_path)
    db.connect()
    
    # 1. Test Schema Creation
    # Check if tables exist
    db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tags'")
    assert db.cursor.fetchone() is not None, "Tags table not created"
    
    db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='image_tags'")
    assert db.cursor.fetchone() is not None, "Image_tags table not created"
    
    # 2. Insert Test Data
    db.add_or_update_image("img1.jpg", 1000, "thumb1.jpg")
    db.add_or_update_image("img2.jpg", 2000, "thumb2.jpg")
    db.commit()
    
    img1_id = db.get_image_id("img1.jpg")
    img2_id = db.get_image_id("img2.jpg")
    
    assert img1_id is not None
    assert img2_id is not None
    
    # 3. Test Tag Creation
    tag1_id = db.get_or_create_tag("Vacation")
    tag2_id = db.get_or_create_tag("Family")
    
    assert tag1_id is not None
    assert tag2_id is not None
    assert tag1_id != tag2_id
    
    # Test duplicate creation returns same ID
    tag1_id_2 = db.get_or_create_tag("Vacation")
    assert tag1_id == tag1_id_2
    
    # 4. Test Adding Tags to Images
    assert db.add_tag_to_image(img1_id, tag1_id) == True # img1 -> Vacation
    assert db.add_tag_to_image(img1_id, tag2_id) == True # img1 -> Family
    assert db.add_tag_to_image(img2_id, tag1_id) == True # img2 -> Vacation
    
    db.commit()
    
    # 5. Test Retrieving Tags
    tags_img1 = db.get_tags_for_image(img1_id)
    tag_names_img1 = [t[1] for t in tags_img1]
    assert "Vacation" in tag_names_img1
    assert "Family" in tag_names_img1
    
    tags_img2 = db.get_tags_for_image(img2_id)
    tag_names_img2 = [t[1] for t in tags_img2]
    assert "Vacation" in tag_names_img2
    assert "Family" not in tag_names_img2
    
    # 6. Test Common Tags
    common = db.get_common_tags_for_images([img1_id, img2_id])
    common_names = [t[1] for t in common]
    assert "Vacation" in common_names
    assert "Family" not in common_names
    
    # 7. Test Filtering (Query Logic)
    # We can simulate the query used in gallery_model
    query = """
        SELECT i.file_path 
        FROM images i
        JOIN image_tags it ON i.id = it.image_id
        WHERE it.tag_id = ?
    """
    db.cursor.execute(query, (tag1_id,))
    results = [r[0] for r in db.cursor.fetchall()]
    assert "img1.jpg" in results
    assert "img2.jpg" in results
    
    db.cursor.execute(query, (tag2_id,))
    results = [r[0] for r in db.cursor.fetchall()]
    assert "img1.jpg" in results
    assert "img2.jpg" not in results
    
    # 8. Test Removal
    db.remove_tag_from_image(img1_id, tag1_id)
    db.commit()
    
    tags_img1 = db.get_tags_for_image(img1_id)
    tag_names_img1 = [t[1] for t in tags_img1]
    assert "Vacation" not in tag_names_img1
    assert "Family" in tag_names_img1
    
    db.close()
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print("All backend tests passed!")

if __name__ == "__main__":
    test_tagging_backend()
