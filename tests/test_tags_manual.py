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
    db.images.add_or_update_image("img1.jpg", 1000, "thumb1.jpg")
    db.images.add_or_update_image("img2.jpg", 2000, "thumb2.jpg")
    db.commit()
    
    img1_id = db.images.get_image_id("img1.jpg")
    img2_id = db.images.get_image_id("img2.jpg")
    
    assert img1_id is not None
    assert img2_id is not None
    
    # 3. Test Tag Creation
    tag1_id = db.tags.get_or_create_tag("Vacation")
    tag2_id = db.tags.get_or_create_tag("Family")
    
    assert tag1_id is not None
    assert tag2_id is not None
    assert tag1_id != tag2_id
    
    # Test duplicate creation returns same ID
    tag1_id_2 = db.tags.get_or_create_tag("Vacation")
    assert tag1_id == tag1_id_2
    
    # 4. Test Adding Tags to Images
    assert db.tags.add_tag_to_image(img1_id, tag1_id) == True # img1 -> Vacation
    assert db.tags.add_tag_to_image(img1_id, tag2_id) == True # img1 -> Family
    assert db.tags.add_tag_to_image(img2_id, tag1_id) == True # img2 -> Vacation
    
    db.commit()
    
    # 5. Test Retrieving Tags
    tags_img1 = db.tags.get_tags_for_image(img1_id)
    tag_names_img1 = [t[1] for t in tags_img1]
    assert "Vacation" in tag_names_img1
    assert "Family" in tag_names_img1
    
    tags_img2 = db.tags.get_tags_for_image(img2_id)
    tag_names_img2 = [t[1] for t in tags_img2]
    assert "Vacation" in tag_names_img2
    assert "Family" not in tag_names_img2
    

    
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
    db.tags.remove_tag_from_image(img1_id, tag1_id)
    db.commit()
    
    tags_img1 = db.tags.get_tags_for_image(img1_id)
    tag_names_img1 = [t[1] for t in tags_img1]
    assert "Vacation" not in tag_names_img1
    assert "Family" in tag_names_img1
    
    db.close()

    # 9. Test Orphan Tag Clean up
    # Re-open for clean state check or continue
    db = Database(db_path)
    db.connect()
    
    # We removed tag1 from img1. It should still be on img2.
    # Verify tag1 still exists in tags table
    db.cursor.execute("SELECT count(*) FROM tags WHERE id = ?", (tag1_id,))
    assert db.cursor.fetchone()[0] == 1, "Tag1 should still exist"
    
    # Remove tag1 from img2 (last usage)
    db.tags.remove_tag_from_image(img2_id, tag1_id)
    db.commit()
    
    # Verify tag1 is GONE from tags table
    db.cursor.execute("SELECT count(*) FROM tags WHERE id = ?", (tag1_id,))
    assert db.cursor.fetchone()[0] == 0, "Tag1 should be deleted after last usage removed"

    # Tag2 ("Family") is on img1. let's check it exists.
    db.cursor.execute("SELECT count(*) FROM tags WHERE id = ?", (tag2_id,))
    assert db.cursor.fetchone()[0] == 1, "Tag2 should still exist"
    
    db.close()
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print("All backend tests passed!")

if __name__ == "__main__":
    test_tagging_backend()
