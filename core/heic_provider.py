from PyQt6.QtQuick import QQuickImageProvider
from PyQt6.QtGui import QImage
from PyQt6.QtCore import QSize
import pillow_heif
from PIL import Image
import os
from urllib.parse import unquote

class HeicImageProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Image)

    def requestImage(self, id, requestedSize):
        """
        id: The file path (passed as string from image://heic/<path>)
        requestedSize: QSize (what the view wants)
        Returns: QImage or (QImage, QSize)
        """
        print(f"HEIC Provider requested: {id}")
        
        # Decode URL (e.g. %20 -> space, %23 -> #)
        file_path = unquote(id)
        
        # Handle Windows paths originating from QUrl (strip leading / if /C:/...)
        if os.name == 'nt' and file_path.startswith('/') and len(file_path) > 2 and file_path[2] == ':':
            file_path = file_path[1:]
            
        # print(f"HEIC Provider resolved path: {file_path}")
        
        if not os.path.exists(file_path):
             # print(f"HEIC Provider: File not found: {file_path}")
             # Return empty/null image
             return QImage(), QSize(0, 0)

        try:
            # Open with Pillow (pillow-heif registered)
            pil_img = Image.open(file_path)
            
            # Force load to catch decoding errors
            pil_img.load()
            
            # Ensure RGB
            if pil_img.mode != "RGB":
                pil_img = pil_img.convert("RGB")
                
            # Convert to QImage
            # 1. Get raw data
            # bytes(pil_img.tobytes(...)) ensures we have a bytes object
            data = pil_img.tobytes("raw", "RGB")
            
            # 2. Create QImage
            # QImage holds a pointer to 'data'. 
            # We use the constructor that takes (data, width, height, bytesPerLine, format)
            # PIL 'tobytes' ("raw", "RGB") is tightly packed, so bytesPerLine = width * 3.
            # If we don't specify this, Qt might assume 32-bit alignment and read invalid memory.
            stride = pil_img.width * 3
            # print(f"HEIC Provider: creating QImage with w={pil_img.width}, h={pil_img.height}, stride={stride}")
            
            qimg = QImage(data, pil_img.width, pil_img.height, stride, QImage.Format.Format_RGB888)
            
            # print("HEIC Provider: QImage created. Copying...")
            
            # 3. Deep copy to ensure QImage owns its own data and is detached from 'data' variable
            qimg = qimg.copy()
            
            # print("HEIC Provider: Copy complete.")
            
            return qimg, QSize(pil_img.width, pil_img.height)

        except Exception as e:
            print(f"Error loading HEIC {file_path}: {e}")
            import traceback
            traceback.print_exc()
            # Return a valid empty image and size to prevent crashes in QML
            return QImage(), QSize(0, 0)
