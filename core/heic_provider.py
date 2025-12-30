from PyQt6.QtQuick import QQuickImageProvider
from PyQt6.QtGui import QImage
from PyQt6.QtCore import QSize
import pillow_heif
from PIL import Image
import os

class HeicImageProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Image)

    def requestImage(self, id, requestedSize):
        """
        id: The file path (passed as string from image://heic/<path>)
        requestedSize: QSize (what the view wants)
        Returns: QImage or (QImage, QSize)
        """
        file_path = id
        
        # Handle potential URL encoding or path issues if necessary
        # Usually internal paths are fine. 
        
        if not os.path.exists(file_path):
             # Return empty/null image
             return QImage(), QSize(0, 0)

        try:
            # Open with Pillow (pillow-heif registered)
            pil_img = Image.open(file_path)
            
            # Ensure RGB
            if pil_img.mode != "RGB":
                pil_img = pil_img.convert("RGB")
                
            # Convert to QImage
            # 1. Get raw data
            data = pil_img.tobytes("raw", "RGB")
            
            # 2. Create QImage
            qimg = QImage(data, pil_img.width, pil_img.height, QImage.Format.Format_RGB888)
            
            # 3. We must keep a reference to the data if QImage doesn't copy it?
            # QImage(bytes, ...) creates a view. We need to copy() to ensure it owns data
            # or ensure 'data' persists. .copy() is safest for a return value.
            qimg = qimg.copy()
            
            return qimg, QSize(pil_img.width, pil_img.height)

        except Exception as e:
            print(f"Error loading HEIC {file_path}: {e}")
            return QImage(), QSize(0, 0)
