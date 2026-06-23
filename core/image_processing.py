import hashlib
import os
import time
from PIL import Image, ExifTags
from core.database import db
from PyQt6.QtCore import QDir
import pillow_heif
import pillow_avif
import pillow_jxl

pillow_heif.register_heif_opener()


def get_date_taken(file_path):
    """
    Extracts the 'Date Taken' from EXIF metadata.
    Returns unix timestamp (int) or None if not found.
    """
    try:
        if not os.path.exists(file_path):
            return None
        
        with Image.open(file_path) as img:
            exif = img.getexif()
            if not exif:
                return None
            
            # DateTimeOriginal (36867), DateTimeDigitized (36868), DateTime (306)
            date_str = exif.get(36867) or exif.get(36868) or exif.get(306)
            
            if not date_str:
                # Check ExifOffset (34665)
                sub_ifd = exif.get_ifd(34665)
                if sub_ifd:
                     date_str = sub_ifd.get(36867) or sub_ifd.get(36868) or sub_ifd.get(306)
            
            if date_str:
                # Format is typically "YYYY:MM:DD HH:MM:SS"
                # Handle potential weirdness or null bytes
                date_str = str(date_str).replace('\x00', '').strip()
                try:
                    import datetime
                    dt = datetime.datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                    return int(dt.timestamp())
                except ValueError:
                    pass
                    
            return None

    except Exception as e:
        # print(f"Error extracting date for {file_path}: {e}")
        return None

def create_and_save_square_thumbnail(image, save_path, size=(128, 128)):
    """
    Creates a square thumbnail from a PIL Image object and saves it to save_path.
    
    Args:
        image (PIL.Image): The source image.
        save_path (str): The path to save the thumbnail to.
        size (tuple): The target size (width, height). Default (128, 128).
    """
    thumb = create_square_thumbnail(image, size)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    thumb.save(save_path, "JPEG")


def create_square_thumbnail(image, size=(128, 128)):
    """
    Creates a square thumbnail from a PIL Image object.
    
    Args:
        image (PIL.Image): The source image.
        size (tuple): The target size (width, height). Default (128, 128).
    
    Returns:
        PIL.Image: The thumbnail image.
    """
    img = image.copy()
    if img.mode != 'RGB':
        img = img.convert('RGB')
        
    # Crop to square
    w, h = img.width, img.height
    if w < h:
        img = img.crop((0, (h - w)/2, w, h-((h-w)/2)))
    else:
        img = img.crop(((w-h)/2, 0, w-((w-h)/2), h))
        
    # Scale
    img.thumbnail(size)
    
    return img


class ImageScanner:
  def __init__(self, thumbnails_dir="thumbnails"):
    self.db = db
    self.thumbnails_dir = thumbnails_dir
    os.makedirs(self.thumbnails_dir, exist_ok=True)

  def scan_and_update_images(self, scan_paths):
    existing_file_stats = self.db.images.get_all_image_paths_and_dates() # {path: last_modified}
    files_to_update = []
    found_files = set()

    # print("Starting fast scan...")
    start_time = time.time()

    # 1. Identify files to process
    for scan_path in scan_paths:
      for root, _, files in os.walk(scan_path):
        for file in files:
          file_path = QDir.cleanPath(os.path.join(root, file))
          
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
                
                # Extract Metadata
                camera, lens = get_camera_lens_info(file_path)
                date_taken = get_date_taken(file_path)
                
                # Fallback to mtime if EXIF date is unavailable
                if not date_taken:
                    date_taken = mtime
                
                files_to_update.append((file_path, mtime, thumb_path, camera, lens, date_taken))

                
          except OSError:
             pass 

    # 2. Update DB in batches (Processing is just DB inserts now, no image IO)
    if files_to_update:
        # print(f"Updating database for {len(files_to_update)} files...")
        batch_count = 0
        for entry in files_to_update:
            self.db.images.add_or_update_image(*entry)
            batch_count += 1
            if batch_count >= 1000:
                self.db.commit()
                batch_count = 0
        self.db.commit()

    # 3. Cleanup missing files
    self.db.images.remove_missing_files(found_files)
    
    # print(f"Scan completed in {time.time() - start_time:.2f} seconds.")
  
  def is_image(self, file_path):
    valid_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".heic", ".heif", ".webp", ".avif", ".jxl"]
    return any(file_path.lower().endswith(ext) for ext in valid_extensions)


def get_exif_string(file_path):
    """
    Extracts basic EXIF data (Focal Length, ISO, Shutter Speed, Aperture) and returns a formatted string.
    Format: "35mm, ISO 64, 1/200 s, ƒ/1.4"
    Returns "Unavailable" if any of the data points are missing.
    """
    try:
        if not os.path.exists(file_path):
            return "Unavailable"

        with Image.open(file_path) as img:
            exif_data = img.getexif()
            if not exif_data:
                return "Unavailable"
            
            # Map tag IDs to names for easier access if needed, but we can look up specific IDs
            # FocalLength: 37386
            # ISOSpeedRatings: 34855
            # ExposureTime: 33434
            # FNumber: 33437
            
            # Extract values
            focal_length = exif_data.get(37386)
            iso = exif_data.get(34855)
            exposure_time = exif_data.get(33434)
            f_number = exif_data.get(33437)
            
            if focal_length is None or iso is None or exposure_time is None or f_number is None:
                # Some cameras might store these in ExifOffset sub-IFD (34665)
                # Let's check there if main tags are missing
                sub_ifd = exif_data.get_ifd(34665)
                if sub_ifd:
                     focal_length = sub_ifd.get(37386, focal_length)
                     iso = sub_ifd.get(34855, iso)
                     exposure_time = sub_ifd.get(33434, exposure_time)
                     f_number = sub_ifd.get(33437, f_number)

            if focal_length is None or iso is None or exposure_time is None or f_number is None:
                return "Unavailable"
            
            # Formatting
            
            try:
                fl_val = float(focal_length)
                # If it's effectively an integer, show as integer
                if fl_val.is_integer():
                     fl_str = f"{int(fl_val)}mm"
                else:
                     fl_str = f"{fl_val:.1f}mm"
            except (ValueError, TypeError):
                 return "Unavailable" # Parsing failed
                 
            # ISO
            # ISO is usually an integer
            iso_str = f"ISO {iso}"
            
            # Exposure Time
            # Usually a float. If < 1, display as fraction (1/x).
            try:
                exp_val = float(exposure_time)
                if exp_val < 1:
                     # approximate fraction
                     denom = int(round(1.0 / exp_val))
                     exp_str = f"1/{denom} s"
                else:
                     exp_str = f"{exp_val} s"
            except (ValueError, TypeError):
                 return "Unavailable"

            # Aperture (FNumber)
            try:
                f_val = float(f_number)
                # Round to 2 decimal places
                f_val = round(f_val, 2)
                f_str = f"ƒ/{f_val}"
            except (ValueError, TypeError):
                 return "Unavailable"
            
            return f"{fl_str}, {iso_str}, {exp_str}, {f_str}"

    except Exception as e:
        print(f"Error reading EXIF for {file_path}: {e}")
        return "Unavailable"

def get_camera_lens_info(file_path):
    """
    Extracts Camera Model and Lens Model from EXIF.
    Returns (camera, lens) tuple.
    """
    try:
        if not os.path.exists(file_path):
            return None, None
        
        with Image.open(file_path) as img:
            exif = img.getexif()
            if not exif:
                return None, None
            
            make = exif.get(271)
            model = exif.get(272)
            
            camera = None
            if model:
                # Clean strings
                model = str(model).replace('\x00', '').strip()
                if make:
                    make = str(make).replace('\x00', '').strip()
                    if make and not model.lower().startswith(make.lower()):
                         camera = f"{make} {model}"
                    else:
                         camera = model
                else:
                    camera = model
            elif make:
                camera = str(make).replace('\x00', '').strip()
                
            # Lens Model (42035 is LensMake, 42036 is LensModel)
            lens = exif.get(42036)
            
            if not lens:
                # Check ExifOffset (34665)
                sub_ifd = exif.get_ifd(34665)
                if sub_ifd:
                    lens = sub_ifd.get(42036)
            
            if lens:
                lens = str(lens).replace('\x00', '').strip()
            
            return camera, lens
            
    except Exception:
        return None, None
