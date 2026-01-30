from PyQt6.QtQuick import QQuickImageProvider
from PyQt6.QtGui import QImage
from PyQt6.QtCore import QSize
import pillow_heif
from PIL import Image
import os
from urllib.parse import unquote


def load_heic_to_qimage(file_path):
    if not os.path.exists(file_path):
          return QImage()

    try:
        # Open with Pillow (pillow-heif registered)
        pil_img = Image.open(file_path)
        
        # Force load to catch decoding errors
        pil_img.load()
        
        # Ensure RGB
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")
            
        # Convert to QImage
        data = pil_img.tobytes("raw", "RGB")
        
        stride = pil_img.width * 3
        qimg = QImage(data, pil_img.width, pil_img.height, stride, QImage.Format.Format_RGB888)
        
        # Deep copy to ensure QImage owns its own data
        qimg = qimg.copy()
        
        return qimg

    except Exception as e:
        print(f"Error loading HEIC {file_path}: {e}")
        # import traceback
        # traceback.print_exc()
        return QImage()

class HeicImageProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Image)

    def requestImage(self, id, requestedSize):
        """
        id: The file path (passed as string from image://heic/<path>)
        requestedSize: QSize (what the view wants)
        Returns: QImage or (QImage, QSize)
        """
        # print(f"HEIC Provider requested: {id}")
        
        # Decode URL (e.g. %20 -> space, %23 -> #)
        file_path = unquote(id)
        
        # Handle Windows paths originating from QUrl (strip leading / if /C:/...)
        if os.name == 'nt' and file_path.startswith('/') and len(file_path) > 2 and file_path[2] == ':':
            file_path = file_path[1:]
            
        # Use helper
        qimg = load_heic_to_qimage(file_path)
        
        return qimg, qimg.size()
