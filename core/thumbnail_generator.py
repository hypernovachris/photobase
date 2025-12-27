import os
import hashlib
from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, QRunnable, QThreadPool
from PIL import Image
from core.image_processing import create_square_thumbnail

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
                self.success_signal.emit(self.file_path, self.thumb_path)
                return

            with Image.open(self.file_path) as img:
                create_square_thumbnail(img, self.thumb_path)
            
            self.success_signal.emit(self.file_path, self.thumb_path)            
        except Exception as e:
            print(f"Error generating thumbnail for {self.file_path}: {e}")
            self.failure_signal.emit(self.file_path)

class ThumbnailGenerator(QObject):
    thumbnailReady = pyqtSignal(str, str) # file_path, thumb_path
    thumbnailFailed = pyqtSignal(str) # file_path

    def __init__(self, parent=None):
        super().__init__(parent)
        self.thread_pool = QThreadPool.globalInstance()
        self.pending_requests = set()
        
        # Queue Management
        self.queue = [] # Stack for LIFO
        self.active_tasks = 0
        self.max_concurrent_tasks = 4 
        self.max_queue_size = 50 
        
        self.thumbnailReady.connect(self._on_thumbnail_ready)
        self.thumbnailFailed.connect(self._on_thumbnail_failed)

    @pyqtSlot(str)
    def request_thumbnail(self, file_path):
        if not file_path:
            return

        thumb_hash = hashlib.md5(file_path.encode()).hexdigest()
        thumb_path = os.path.join("thumbnails", f"{thumb_hash}.jpg")

        if os.path.exists(thumb_path):
            self.thumbnailReady.emit(file_path, thumb_path)
            return

        if file_path in self.pending_requests:
            return

        # Add to queue
        self.pending_requests.add(file_path)
        self.queue.append((file_path, thumb_path))
        
        # Enforce max queue size (drop oldest)
        if len(self.queue) > self.max_queue_size:
            dropped_file, _ = self.queue.pop(0) # Pop from start (oldest)
            if dropped_file in self.pending_requests:
                self.pending_requests.remove(dropped_file)

        self.process_queue()

    def process_queue(self):
        while self.active_tasks < self.max_concurrent_tasks and self.queue:
            # Pop from end (LIFO - newest first)
            file_path, thumb_path = self.queue.pop() 
            
            self.active_tasks += 1
            runnable = ThumbnailRunnable(file_path, thumb_path, self.thumbnailReady, self.thumbnailFailed)
            self.thread_pool.start(runnable)

    # Success handler
    def _on_thumbnail_ready(self, file_path, thumb_path):
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

    @pyqtSlot(int)
    def setMaxQueueSize(self, size):
        if size < 1:
            size = 1
        self.max_queue_size = size
        # print(f"Thumbnail queue limit set to {size}")
        
        # Trim queue if needed (drop oldest)
        while len(self.queue) > self.max_queue_size:
            dropped_file, _ = self.queue.pop(0)
            if dropped_file in self.pending_requests:
                self.pending_requests.remove(dropped_file)
