import os
import hashlib
from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, QRunnable, QThreadPool
from PIL import Image, ImageOps
from core.image_processing import create_and_save_square_thumbnail

class ThumbnailRunnable(QRunnable):
    def __init__(self, file_path, thumb_path, success_signal, failure_signal):
        super().__init__()
        self.file_path = file_path
        self.thumb_path = thumb_path
        self.success_signal = success_signal
        self.failure_signal = failure_signal

    def run(self):
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.thumb_path), exist_ok=True)
            
            # Double check inside thread
            if os.path.exists(self.thumb_path):
                self.success_signal.emit(self.file_path)
                return

            with Image.open(self.file_path) as img:
                img = ImageOps.exif_transpose(img)
                create_and_save_square_thumbnail(img, self.thumb_path)
            
            self.success_signal.emit(self.file_path)            
        except Exception as e:
            print(f"Error generating thumbnail for {self.file_path}: {e}")
            self.failure_signal.emit(self.file_path)

class ThumbnailGenerator(QObject):
    thumbnailReady = pyqtSignal(str) # file_path
    thumbnailFailed = pyqtSignal(str) # file_path
    queueEmpty = pyqtSignal()

    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = ThumbnailGenerator()
        return cls._instance

    def __init__(self, parent=None):
        if ThumbnailGenerator._instance is not None:
             raise Exception("This class is a singleton!")
        else:
             super().__init__(parent)
             ThumbnailGenerator._instance = self
             
        self.thread_pool = QThreadPool.globalInstance()
        self.pending_requests = set()
        
        # Queue Management
        self.queue = [] # Stack for LIFO (list of (file_path, thumb_path))
        self.active_tasks = 0
        self.max_concurrent_tasks = 4
        self.max_queue_size = 50 
        
        self.thumbnailReady.connect(self._on_thumbnail_ready)
        self.thumbnailFailed.connect(self._on_thumbnail_failed)

    @pyqtSlot(str)
    @pyqtSlot(int, str)
    def request_thumbnail(self, index_or_path, file_path=None):
        if file_path is None:
            # Called with path only: request_thumbnail(file_path)
            actual_path = index_or_path
        else:
            # Called with index and path (legacy): request_thumbnail(index, file_path)
            actual_path = file_path

        if not actual_path:
            return

        thumb_hash = hashlib.md5(actual_path.encode()).hexdigest()
        thumb_path = os.path.join("thumbnails", f"{thumb_hash}.jpg")

        if os.path.exists(thumb_path):
            self.thumbnailReady.emit(actual_path)
            return

        if actual_path in self.pending_requests:
            return

        # Add to queue
        self.pending_requests.add(actual_path)
        self.queue.append((actual_path, thumb_path))
        
        # Enforce max queue size (drop oldest)
        if len(self.queue) > self.max_queue_size:
            dropped_path, _ = self.queue.pop(0) # Pop from start (oldest)
            if dropped_path in self.pending_requests:
                self.pending_requests.remove(dropped_path)

        self.process_queue()

    def process_queue(self):
        while self.active_tasks < self.max_concurrent_tasks and self.queue:
            # Pop from end (LIFO - newest first)
            file_path, thumb_path = self.queue.pop() 
            
            self.active_tasks += 1
            runnable = ThumbnailRunnable(file_path, thumb_path, self.thumbnailReady, self.thumbnailFailed)
            self.thread_pool.start(runnable)
            
        if self.active_tasks == 0 and not self.queue:
            self.queueEmpty.emit()

    # Success handler
    def _on_thumbnail_ready(self, file_path):
        if file_path in self.pending_requests:
            self.pending_requests.remove(file_path)
        
        self.active_tasks -= 1
        # Process next in queue
        self.process_queue()

    # Failure handler
    def _on_thumbnail_failed(self, file_path):
        if file_path in self.pending_requests:
            self.pending_requests.remove(file_path)
            
        self.active_tasks -= 1
        # Process next in queue
        self.process_queue()

    def clearQueue(self):
        self.queue.clear()
        self.pending_requests.clear()

    @pyqtSlot(int)
    def setMaxQueueSize(self, size):
        if size < 1:
            size = 1
        self.max_queue_size = size
        
        # Trim queue if needed (drop oldest)
        while len(self.queue) > self.max_queue_size:
            dropped_path, _ = self.queue.pop(0)
            if dropped_path in self.pending_requests:
                self.pending_requests.remove(dropped_path)
