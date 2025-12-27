import os
import sys
import sqlite3
import numpy as np
from PIL import Image
import face_recognition

# Setup paths
sys.path.append(os.getcwd())
from core.database import Database


def debug_scan():
    print("Initializing Database...")
    db = Database()
    db.connect()
    
    # Check existing data
    db.cursor.execute("SELECT COUNT(*) FROM faces")
    face_count = db.cursor.fetchone()[0]
    print(f"Total faces in DB: {face_count}")

    db.cursor.execute("SELECT COUNT(*) FROM images")
    image_count = db.cursor.fetchone()[0]
    print(f"Total images in DB: {image_count}")

    count = db.get_unscanned_count()
    print(f"Unscanned images count: {count}")
    


    # Manual override for testing specific file
    debug_files = [r"D:\Pictures\11-23-25-11-29-25\DSC_0130.JPG"]


    import math
    from PIL import ImageOps
    max_pixels = 2000000

    for file_path in debug_files:
        print(f"\n--- Testing scan on: {file_path} ---")
        
        if not os.path.exists(file_path):
            print("File does not exist!")
            continue

        try:
            pil_image = Image.open(file_path)
            # if pil_image.mode != 'RGB':
            #     pil_image = pil_image.convert('RGB')
            
            w, h = pil_image.size
            print(f"Original size: {w}x{h}")
            
            # Check EXIF
            exif = pil_image._getexif()
            orientation = exif.get(0x0112) if exif else None
            print(f"EXIF Orientation: {orientation}")

            # Test 1: Original Raw (Current behavior)
            print("1. Detecting on RAW ORIGINAL...")
            if pil_image.mode != 'RGB':
                img_1 = pil_image.convert('RGB')
            else:
                img_1 = pil_image
            
            image = np.array(img_1)
            locs = face_recognition.face_locations(image)
            print(f"   Found {len(locs)} faces.")
            
            # Test 2: EXIF Transposed (Corrected)
            print("2. Detecting on EXIF CORRECTED...")
            # Reload to be safe
            pil_image = Image.open(file_path)
            pil_image = ImageOps.exif_transpose(pil_image)
            
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            w_corr, h_corr = pil_image.size
            print(f"   Corrected size: {w_corr}x{h_corr}")

            image_corr = np.array(pil_image)
            locs_corr = face_recognition.face_locations(image_corr)
            print(f"   Found {len(locs_corr)} faces.")

            # Test 3: EXIF Corrected + Resized
            print("3. Detecting on EXIF CORRECTED + RESIZED...")
            
            if w_corr * h_corr > max_pixels:
                scale = math.sqrt(max_pixels / (w_corr * h_corr))
                new_w = int(w_corr * scale)
                new_h = int(h_corr * scale)
                print(f"   Resizing to {new_w}x{new_h} (Scale: {scale:.2f})...")
                resized_pil = pil_image.resize((new_w, new_h))
                resized_image = np.array(resized_pil)
                locs_resized = face_recognition.face_locations(resized_image)
                print(f"   Found {len(locs_resized)} faces.")
            else:
                print("   Skipped resize.")

        except Exception as e:
            print(f"Error scanning {file_path}: {e}")




if __name__ == "__main__":
    debug_scan()
