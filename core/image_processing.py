import hashlib
import os
import time
from core.database import db

class ImageScanner:
  def __init__(self, thumbnails_dir="thumbnails"):
    self.db = db
    self.thumbnails_dir = thumbnails_dir
    os.makedirs(self.thumbnails_dir, exist_ok=True)

  def scan_and_update_images(self, scan_paths):
    existing_file_stats = self.db.get_all_image_paths_and_dates() # {path: last_modified}
    files_to_update = []
    found_files = set()

    print("Starting fast scan...")
    start_time = time.time()

    # 1. Identify files to process
    for scan_path in scan_paths:
      for root, _, files in os.walk(scan_path):
        for file in files:
          file_path = os.path.join(root, file)
          
          if not self.is_image(file_path):
            continue

          found_files.add(file_path)
          
          try:
            mtime = int(os.path.getmtime(file_path))
            
            # Check if new or modified
            if file_path not in existing_file_stats or existing_file_stats[file_path] != mtime:
                # Calculate expected thumbnail path (hash of file path)
                thumb_hash = hashlib.md5(file_path.encode()).hexdigest()
                thumb_path = os.path.join(self.thumbnails_dir, f"{thumb_hash}.jpg")
                files_to_update.append((file_path, mtime, thumb_path))
                
          except OSError:
             pass 

    # 2. Update DB in batches (Processing is just DB inserts now, no image IO)
    if files_to_update:
        print(f"Updating database for {len(files_to_update)} files...")
        batch_count = 0
        for entry in files_to_update:
            self.db.add_or_update_image(*entry)
            batch_count += 1
            if batch_count >= 1000:
                self.db.commit()
                batch_count = 0
        self.db.commit()

    # 3. Cleanup missing files
    self.db.remove_missing_files(found_files)
    
    print(f"Scan completed in {time.time() - start_time:.2f} seconds.")
  
  def is_image(self, file_path):
    valid_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
    return any(file_path.lower().endswith(ext) for ext in valid_extensions)