
import face_recognition
from PIL import Image
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread, QRunnable, QThreadPool
from core.database import db
import os

class FaceScannerWorker(QRunnable):
    def __init__(self, signals):
        super().__init__()
        self.signals = signals
        self.is_running = True

    def run(self):
        try:
            db.connect()
            unscanned = db.get_unscanned_images()
            total = len(unscanned)
            
            if total == 0:
                self.signals.finished.emit()
                db.close()
                return

            # Load known faces to memory for this batch to speed up matching
            # Format: list of (person_id, encoding)
            known_faces = db.get_all_face_encodings()
            known_encodings = [np.frombuffer(enc, dtype=np.float64) for _, enc in known_faces]
            known_ids = [pid for pid, _ in known_faces]

            processed = 0
            
            for image_id, file_path in unscanned:
                if not self.is_running:
                    break
                
                if not os.path.exists(file_path):
                     # Mark as scanned so we don't retry forever? Or ignore.
                     # Mark as scanned to skip next time.
                     db.mark_image_scanned(image_id)
                     processed += 1
                     self.signals.progress.emit(processed, total)
                     continue

                try:
                    # Load image with PIL to allow resizing
                    pil_image = Image.open(file_path)

                    # Ensure RGB
                    if pil_image.mode != 'RGB':
                        pil_image = pil_image.convert('RGB')

                    original_w, original_h = pil_image.size
                    
                    # # Resize if too large
                    # max_dim = 1000
                    # scale = 1.0
                    
                    # if max(original_w, original_h) > max_dim:
                    #     scale = max_dim / max(original_w, original_h)
                    #     new_w = int(original_w * scale)
                    #     new_h = int(original_h * scale)
                    #     pil_image = pil_image.resize((new_w, new_h))
                    
                    # image = np.array(pil_image)

                    # Resize if too large
                    max_mp = 2000000
                    scale = 1.0

                    if original_w * original_h > max_mp:
                        scale = math.sqrt(max_mp / (original_w * original_h))
                        new_w = int(original_w * scale)
                        new_h = int(original_h * scale)
                        pil_image = pil_image.resize((new_w, new_h))
                    
                    image = np.array(pil_image)
                    
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
                            person_id = db.create_person()
                            known_encodings.append(encoding)
                            known_ids.append(person_id)
                        
                        # Save face
                        # face_recognition returns (top, right, bottom, left)
                        # We want x, y, w, h
                        x, y, w, h = left, top, right - left, bottom - top
                        db.add_face(image_id, person_id, encoding, (x, y, w, h))
                    
                    db.mark_image_scanned(image_id)
                    db.commit() # Commit per image to be safe? Or every N. Per image is safer for interruptions.
                    
                except Exception as e:
                    print(f"Error scanning {file_path}: {e}")
                    # Mark scanned anyway to avoid freeze on bad file?
                    db.mark_image_scanned(image_id)
                    db.commit()

                processed += 1
                self.signals.progress.emit(processed, total)

            self.signals.finished.emit()
            db.close()
            
        except Exception as e:
            print(f"Scanner crashed: {e}")
            self.signals.finished.emit()
            if db.connection:
                db.close()

    def stop(self):
        self.is_running = False

class ScannerSignals(QObject):
    started = pyqtSignal()
    progress = pyqtSignal(int, int) # processed, total
    finished = pyqtSignal()

class FaceScanner(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.signals = ScannerSignals()
        self.thread_pool = QThreadPool.globalInstance()
        self.worker = None

    @pyqtSlot()
    def start_scan(self):
        if self.worker is not None and self.worker.is_running:
            return
            
        self.worker = FaceScannerWorker(self.signals)
        self.signals.started.emit()
        self.thread_pool.start(self.worker)

    @pyqtSlot()
    def stop_scan(self):
        if self.worker:
            self.worker.stop()
            self.worker = None

