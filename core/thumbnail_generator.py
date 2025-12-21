import os
import hashlib
from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, QRunnable, QThreadPool
from PIL import Image

class ThumbnailRunnable(QRunnable):
    def __init__(self, file_path, thumb_path, callback):
        super().__init__()
        self.file_path = file_path
        self.thumb_path = thumb_path
        self.callback = callback

    def run(self):
        try:
            # Ensure directory exists (just in case)
            os.makedirs(os.path.dirname(self.thumb_path), exist_ok=True)
            
            # Double check inside thread to avoid race conditions or wasted work
            if os.path.exists(self.thumb_path):
                self.callback.emit(self.file_path, self.thumb_path)
                return

            with Image.open(self.file_path) as img:
                img = img.convert('RGB')
                # crop the image to square
                w, h = img.width, img.height
                if img.width < img.height:
                    cropped = img.crop((0, (h - w)/2, w, h-((h-w)/2)))
                else:
                    cropped = img.crop(((w-h)/2, 0, w-((w-h)/2), h))
                # scale and save
                cropped.thumbnail((128, 128))
                cropped.save(self.thumb_path)
            
            self.callback.emit(self.file_path, self.thumb_path)
            
        except Exception as e:
            print(f"Error generating thumbnail for {self.file_path}: {e}")

class ThumbnailGenerator(QObject):
    thumbnailReady = pyqtSignal(str, str) # file_path, thumb_path

    def __init__(self, parent=None):
        super().__init__(parent)
        self.thread_pool = QThreadPool.globalInstance()
        self.pending_requests = set()

    @pyqtSlot(str)
    def request_thumbnail(self, file_path):
        if not file_path:
            return

        thumb_hash = hashlib.md5(file_path.encode()).hexdigest()
        thumb_path = os.path.join("thumbnails", f"{thumb_hash}.jpg")

        if os.path.exists(thumb_path):
            # Signal immediately if ready (optional, but helps UI update if it was stuck)
            self.thumbnailReady.emit(file_path, thumb_path)
            return

        if file_path in self.pending_requests:
            return

        self.pending_requests.add(file_path)
        
        runnable = ThumbnailRunnable(file_path, thumb_path, self.thumbnailReady)
        # We need a way to clean up pending_requests. 
        # Since Runnable signals back, we can just remove it then? 
        # But QRunnable doesn't support slots directly easily without another object.
        # Actually, let's just use the signal we emit.
        
        # Connect strictly to a cleanup slot, but signals across threads... 
        # simplest is to just accept we might work twice in rare race cases, 
        # or use a QObject wrapper for the runnable signals.
        # For now, let's just fire and forget, the set check reduces spam.
        
        self.thread_pool.start(runnable)

    # We hook into our own signal to clear the pending set
    def _on_thumbnail_ready(self, file_path, thumb_path):
        if file_path in self.pending_requests:
            self.pending_requests.remove(file_path)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.thread_pool = QThreadPool.globalInstance()
        self.pending_requests = set()
        self.thumbnailReady.connect(self._on_thumbnail_ready)
