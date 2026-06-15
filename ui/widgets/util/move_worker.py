import os
import shutil
import hashlib
from PyQt6.QtCore import QThread, pyqtSignal

class MoveWorker(QThread):
    progress = pyqtSignal(int, int) # current, total
    fileMoved = pyqtSignal(str, str, str) # old_path, new_path, new_thumb_path
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, paths, dest_dir):
        super().__init__()
        self.paths = paths
        self.dest_dir = dest_dir

    def run(self):
        try:
            total = len(self.paths)
            for i, old_path in enumerate(self.paths):
                if not os.path.exists(old_path):
                    self.progress.emit(i + 1, total)
                    continue
                
                filename = os.path.basename(old_path)
                new_path = os.path.join(self.dest_dir, filename)
                
                # Check if moving to same path or if file already exists at dest
                if os.path.abspath(old_path) == os.path.abspath(new_path) or os.path.exists(new_path):
                    self.progress.emit(i + 1, total)
                    continue
                
                # Move file
                shutil.move(old_path, new_path)
                
                # Deal with thumbnail
                old_thumb_hash = hashlib.md5(old_path.encode()).hexdigest()
                old_thumb_path = os.path.join("thumbnails", f"{old_thumb_hash}.jpg")
                
                new_thumb_hash = hashlib.md5(new_path.encode()).hexdigest()
                new_thumb_path = os.path.join("thumbnails", f"{new_thumb_hash}.jpg")
                
                if os.path.exists(old_thumb_path):
                    # Ensure thumbnails directory exists
                    os.makedirs("thumbnails", exist_ok=True)
                    try:
                        shutil.move(old_thumb_path, new_thumb_path)
                    except OSError:
                        pass
                
                self.fileMoved.emit(old_path, new_path, new_thumb_path)
                self.progress.emit(i + 1, total)
                
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
