from PIL import Image
import hashlib
import time
import os
from core.database import db

class ImageScanner:
  def __init__(self, thumbnails_dir="thumbnails"):
    self.db = db
    self.thumbnails_dir = thumbnails_dir
    os.makedirs(self.thumbnails_dir, exist_ok=True)

  def generate_thumbnail(self, image_path):
    thumb_hash = hashlib.md5(image_path.encode()).hexdigest()
    thumb_path = os.path.join(self.thumbnails_dir, f"{thumb_hash}.jpg")

    if not os.path.exists(thumb_path):
      with Image.open(image_path) as img:
        img.thumbnail((128, 128))
        img.save(thumb_path)
    return thumb_path

  def scan_and_update_images(self, scan_paths):
    existing_files = set()
    for scan_path in scan_paths:
      for root, _, files in os.walk(scan_path):
        for file in files:
          file_path = os.path.join(root, file)
          
          if not self.is_image(file_path):
            continue

          existing_files.add(file_path)

          last_modified = int(os.path.getmtime(file_path))
          #thumbnail_path = self.generate_thumbnail(file_path)

          # check if image exists in DB
          self.db.cursor.execute("SELECT last_modified FROM images WHERE file_path = ?", (file_path,))
          existing_entry = self.db.cursor.fetchone()

          if existing_entry:
            # image exists, check if modified
            db_last_modified = existing_entry[0]
            if db_last_modified != last_modified:
              # first, let's delete the old, outdated thumbnail. query db for old path:
              self.db.cursor.execute("SELECT thumbnail_path FROM images WHERE file_path = ?", (file_path,))
              old_thumb_path = self.db.cursor.fetchone()
              if old_thumb_path:
                old_thumb_path = old_thumb_path[0]
                # now remove it.
                if os.path.exists(old_thumb_path):
                  # all of these if statements should pass unless something bad has happened.
                  os.remove(old_thumb_path)
              # now update the entry
              thumbnail_path = self.generate_thumbnail(file_path)
              self.db.delete_image(file_path)
              self.db.add_or_update_image(file_path, last_modified, thumbnail_path)
          else:
            # image DNE, add to DB
            thumbnail_path = self.generate_thumbnail(file_path)
            self.db.add_or_update_image(file_path, last_modified, thumbnail_path)
    
    # in the following function, we also remove thumbnails for images no longer in the DB
    self.db.remove_missing_files(existing_files)
  
  def is_image(self, file_path):
    valid_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
    return any(file_path.lower().endswith(ext) for ext in valid_extensions)