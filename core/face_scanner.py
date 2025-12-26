
import face_recognition
from PIL import Image
import numpy as np
import time
import math
import hashlib
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread, QRunnable, QThreadPool, QTimer, pyqtProperty
from core.database import Database
import os


class FaceScannerWorker(QObject):
    def __init__(self, signals):
        super().__init__()
        self.signals = signals
        self.is_running = True
        self.db = None

    @pyqtSlot()
    def run(self):
        try:
            self.db = Database()
            self.db.connect()
            
            thumbnails_dir = "thumbnails"
            os.makedirs(thumbnails_dir, exist_ok=True)
            
            while self.is_running:
                # Fetch a small batch of unscanned images
                unscanned = self.db.get_unscanned_images(limit=5)
                
                if not unscanned:
                    # No images to scan, wait and poll again
                    # Sleep in small chunks to allow quick stopping
                    for _ in range(20): # 2 seconds total
                        if not self.is_running:
                            break
                        time.sleep(0.1)
                    continue

                # Load known faces to memory for this batch to speed up matching
                known_faces = self.db.get_all_face_encodings()
                known_encodings = [np.frombuffer(enc, dtype=np.float64) for _, enc in known_faces]
                known_ids = [pid for pid, _ in known_faces]

                processed_in_batch = 0
                
                for image_id, file_path in unscanned:
                    if not self.is_running:
                        break
                    
                    if not os.path.exists(file_path):
                         self.db.mark_image_scanned(image_id)
                         self.db.commit()
                         continue

                    try:
                        # Load image with PIL to allow resizing
                        pil_image = Image.open(file_path)

                        # Ensure RGB
                        if pil_image.mode != 'RGB':
                            pil_image = pil_image.convert('RGB')

                        original_w, original_h = pil_image.size
                        
                        # Generate thumbnail if missing
                        thumb_hash = hashlib.md5(file_path.encode()).hexdigest()
                        thumb_path = os.path.join(thumbnails_dir, f"{thumb_hash}.jpg")
                        
                        if not os.path.exists(thumb_path):
                            try:
                                thumb_size = (300, 300)
                                thumb_img = pil_image.copy()
                                thumb_img.thumbnail(thumb_size)
                                thumb_img.save(thumb_path, "JPEG")
                                # Update DB with thumbnail path
                                mtime = int(os.path.getmtime(file_path))
                                self.db.add_or_update_image(file_path, mtime, thumb_path)
                            except Exception as e:
                                print(f"Error generating thumbnail for {file_path}: {e}")

                        # Resize if too large for face scanning
                        max_mp = 2000000
                        scale = 1.0

                        if original_w * original_h > max_mp:
                            scale = math.sqrt(max_mp / (original_w * original_h))
                            new_w = int(original_w * scale)
                            new_h = int(original_h * scale)
                            pil_image = pil_image.resize((new_w, new_h))
                        
                        image = np.array(pil_image)
                        image = np.ascontiguousarray(image, dtype=np.uint8)
                        
                        # Idempotency: Clear existing faces for this image before adding new ones
                        self.db.clear_faces_for_image(image_id)
                        
                        # Detect faces
                        face_locations = face_recognition.face_locations(image)
                        face_encodings = face_recognition.face_encodings(image, face_locations)

                        for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
                            # Scale back coordinates if we resized
                            if scale != 1.0:
                                top = int(top / scale)
                                right = int(right / scale)
                                bottom = int(bottom / scale)
                                left = int(left / scale)

                            # Match against known
                            matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=0.6)
                            person_id = None
                            
                            if True in matches:
                                first_match_index = matches.index(True)
                                person_id = known_ids[first_match_index]
                            else:
                                # Create new person
                                person_id = self.db.create_person()
                                known_encodings.append(encoding)
                                known_ids.append(person_id)
                            
                            # Save face
                            x, y, w, h = left, top, right - left, bottom - top
                            self.db.add_face(image_id, person_id, encoding, (x, y, w, h))
                        
                        self.db.mark_image_scanned(image_id)
                        self.db.commit()
                        
                    except Exception as e:
                        print(f"Error scanning {file_path}: {e}")
                        self.db.mark_image_scanned(image_id)
                        self.db.commit()

                    processed_in_batch += 1
                
            if self.db:
                self.db.close()
            
            try:
                self.signals.finished.emit()
            except RuntimeError:
                pass
            
        except Exception as e:
            print(f"Scanner crashed: {e}")
            if self.db and self.db.connection:
                self.db.close()
            try:
                self.signals.finished.emit()
            except RuntimeError:
                pass

    def stop(self):
        self.is_running = False

class ScannerSignals(QObject):
    started = pyqtSignal()
    finished = pyqtSignal()
    unscanned_count_changed = pyqtSignal(int)

class FaceScanner(QObject):
    unscannedCountChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.signals = ScannerSignals()
        self.worker = None
        self.thread = None
        self.db = Database() # For initial count checking
        self.db.connect()
        
        self._unscanned_count = 0
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.check_status)
        self.update_timer.start(1000) # Check every second
        
        self.check_status() # Initial check

    @pyqtProperty(int, notify=unscannedCountChanged)
    def unscanned_count(self):
        return self._unscanned_count

    def check_status(self):
        try:
            count = self.db.get_unscanned_count()
            if count != self._unscanned_count:
                self._unscanned_count = count
                self.unscannedCountChanged.emit(count)
        except Exception:
            pass

    @pyqtSlot()
    def start_scan(self):
        if self.thread and self.thread.isRunning():
            return
            
        print("Starting single background scanner thread...")
        
        self.thread = QThread()
        self.worker = FaceScannerWorker(self.signals)
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.signals.finished.connect(self.thread.quit)
        self.signals.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self._on_thread_finished)
        
        self.thread.start()
        self.signals.started.emit()

    def _on_thread_finished(self):
        self.thread = None
        self.worker = None

    @pyqtSlot()
    def stop_scan(self):
        if self.worker:
            self.worker.stop()
        # Thread will quit when worker emits finished

