
import face_recognition
from PIL import Image, ImageOps
import numpy as np
import time
import math
import hashlib
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread, QRunnable, QThreadPool, QTimer, pyqtProperty
from core.database import Database
import os
from core.image_processing import create_square_thumbnail

thumbnails_dir = "thumbnails"

def score_face_thumbnail(landmarks):
    score = 0.5 # Default
    try:
        l_eye = np.mean(landmarks['left_eye'], axis=0) # [x, y]
        r_eye = np.mean(landmarks['right_eye'], axis=0)
        nose = np.mean(landmarks['nose_bridge'], axis=0)
        
        # Centroid of eyes
        eyes_center = (l_eye + r_eye) / 2
        
        # Deviation of nose from eye center (horizontal)
        # We want nose.x to be close to eyes_center.x
        diff_x = abs(nose[0] - eyes_center[0])
        eye_dist = np.linalg.norm(l_eye - r_eye)
        
        # Normalize diff by eye distance
        if eye_dist > 0:
            normalized_diff = diff_x / eye_dist
            # Lower diff is better. 
            # If normalized_diff is 0, score is 1.0. If 0.5, score is 0.5.
            score = max(0.0, 1.0 - normalized_diff)
    except Exception:
        pass
    return score

class FaceScannerWorker(QObject):
    def __init__(self, signals, worker_id):
        super().__init__()
        self.signals = signals
        self.worker_id = worker_id
        self.is_running = True
        self.db = None

    @pyqtSlot()
    def run(self):
        try:
            self.db = Database()
            self.db.connect()
            
            # Reduce thread priority
            # self.thread().setPriority(QThread.Priority.LowPriority) 
            # (Note: QThread priority is set on the thread object, not self.thread() usually, or via currentThread in run)
            
            while self.is_running:
                # Claim a batch
                try:
                    unscanned = self.db.claim_unscanned_images(limit=5)
                except Exception as e:
                    print(f"Worker {self.worker_id} DB Error claiming: {e}")
                    time.sleep(1)
                    continue

                if not unscanned:
                    # No work, sleep and standard polling
                    for _ in range(20): # 2 seconds total
                        if not self.is_running:
                            break
                        time.sleep(0.1)
                    continue
                
                processed_in_batch = 0
                
                for image_id, file_path in unscanned:

                    try:
                        known_faces = self.db.get_all_face_encodings()
                        known_encodings = [np.frombuffer(enc, dtype=np.float64) for _, enc in known_faces]
                        known_ids = [pid for pid, _ in known_faces]
                    except Exception as e:
                        print(f"Worker {self.worker_id} Error fetching faces: {e}")
                        continue
                    
                    if not self.is_running:
                        # We claimed them but stopping. They stay -1.
                        # `reset_stuck_scans` on next startup fixes this.
                        break
                    
                    if not os.path.exists(file_path):
                         self.db.mark_image_scanned(image_id)
                         self.db.commit()
                         continue

                    try:
                        # 1. Load original image
                        try:
                            pil_original = Image.open(file_path)
                            pil_original = ImageOps.exif_transpose(pil_original)
                        except Exception as e:
                             print(f"Worker {self.worker_id} Error loading image: {e}")
                             self.db.mark_image_scanned(image_id)
                             self.db.commit()
                             continue

                        if pil_original.mode != 'RGB':
                            pil_original = pil_original.convert('RGB')
                        
                        image_original_np = np.array(pil_original)
                        
                        original_w, original_h = pil_original.size
                        
                        # 2. Prepare detection image (resized if needed)
                        max_pixels = 2000000 # 2MP
                        detection_scale = 1.0
                        image_for_detection = image_original_np

                        if original_w * original_h > max_pixels:
                            # print(f"Worker {self.worker_id} Resizing for detection {file_path}")
                            detection_scale = math.sqrt(max_pixels / (original_w * original_h))
                            new_w = int(original_w * detection_scale)
                            new_h = int(original_h * detection_scale)
                            pil_small = pil_original.resize((new_w, new_h))
                            image_for_detection = np.array(pil_small)
                            image_for_detection = np.ascontiguousarray(image_for_detection, dtype=np.uint8)
                        
                        # 3. Detect faces (on (possibly) resized image)
                        # print(f"Worker {self.worker_id} Detecting faces in {file_path} ({image_for_detection.shape})...")
                        face_locations_small = face_recognition.face_locations(image_for_detection)
                        # print(f"Worker {self.worker_id} Detection done. Found {len(face_locations_small)}.")
                        
                        if not face_locations_small:
                            self.db.mark_image_scanned(image_id)
                            self.db.commit()
                            continue

                        # 4. Scale locations BACK to original coordinates immediately
                        face_locations = []
                        if detection_scale != 1.0:
                            for top, right, bottom, left in face_locations_small:
                                face_locations.append((
                                    int(top / detection_scale),
                                    int(right / detection_scale),
                                    int(bottom / detection_scale),
                                    int(left / detection_scale)
                                ))
                        else:
                            face_locations = face_locations_small

                        # Remove faces that are too small
                        face_locations = [face for face in face_locations if face[2] - face[0] > 150]

                        #print(f"Worker {self.worker_id}: Found {len(face_locations)} faces in {file_path}")

                        # 5. Use ORIGINAL image for encoding and landmarks (Accuracy)
                        # print(f"Worker {self.worker_id} Encoding faces in {file_path} ({image_original_np.shape})...")
                        face_encodings = face_recognition.face_encodings(image_original_np, face_locations, model='large')
                        
                        # print(f"Worker {self.worker_id} Getting landmarks for {file_path} ({image_original_np.shape})...")
                        face_landmarks_list = face_recognition.face_landmarks(image_original_np, face_locations)

                        for i, ((top, right, bottom, left), encoding, landmarks) in enumerate(zip(face_locations, face_encodings, face_landmarks_list)):
                            # Coordinates are already in original scale
                            
                            # --- Calculate Quality Score ---
                            # Use helper
                            score = score_face_thumbnail(landmarks)

                            # If no known encodings, create a new person
                            if len(known_encodings) == 0:
                                person_id = self.db.create_person()
                                known_encodings.append(encoding)
                                known_ids.append(person_id)
                            else:
                                # Get the distance to every other face
                                distances = face_recognition.face_distance(known_encodings, encoding)
                                # Find the closest match
                                closest_match_index = distances.argmin()
                                # Check if it's the same person
                                is_same_person = face_recognition.compare_faces([known_encodings[closest_match_index]], encoding, tolerance=0.6)[0]
                            
                                if is_same_person:
                                    person_id = known_ids[closest_match_index]
                                    # remove the encoding from the list to avoid matching it again in the same image
                                    known_encodings.pop(closest_match_index)
                                    known_ids.pop(closest_match_index)
                                else:
                                    person_id = self.db.create_person()

                            
                            # Check if this face is a better cover photo
                            current_best = self.db.get_person_score(person_id)
                            
                            if score > current_best:
                                try:
                                    uuid = self.db.get_person_uuid(person_id)
                                    if uuid:
                                        face_thumb_dir = os.path.join(thumbnails_dir, "faces")
                                        os.makedirs(face_thumb_dir, exist_ok=True)
                                        face_thumb_path = os.path.join(face_thumb_dir, f"{uuid}.jpg")
                                        
                                        # Crop from ORIGINAL high-res image
                                        pad_w = int((right - left) * 0.2)
                                        pad_h = int((bottom - top) * 0.2)
                                        
                                        crop_left = max(0, left - pad_w)
                                        crop_top = max(0, top - pad_h)
                                        crop_right = min(original_w, right + pad_w)
                                        crop_bottom = min(original_h, bottom + pad_h)
                                        
                                        face_crop = pil_original.crop((crop_left, crop_top, crop_right, crop_bottom))
                                        
                                        create_square_thumbnail(face_crop).save(face_thumb_path, "JPEG", quality=90)
                                        
                                        self.db.update_person_cover_score(person_id, score)
                                except Exception as e:
                                    print(f"Error updating cover for person {person_id}: {e}")
                            
                            # Save face (simplified)
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
        
            
        except Exception as e:
            print(f"Scanner crashed: {e}")
            if self.db and self.db.connection:
                self.db.close()

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
        self.workers = []
        self.threads = []
        
        self.db = Database() # For initial count checking
        self.db.connect()
        self.db.reset_stuck_scans() # Reset any -1 from previous bad runs
        
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
            # Note: get_unscanned_count counts '0'. '-1' is effectively hidden/processing.
            if count != self._unscanned_count:
                self._unscanned_count = count
                self.unscannedCountChanged.emit(count)
        except Exception:
            pass

    @pyqtSlot()
    def start_scan(self):
        if self.threads:
            # Already running
            return
            
        # print("Starting multithreaded background scanner...")
        
        # DEBUG: Reduced to 1 thread to isolate crash cause
        thread_count = 1
        
        for i in range(thread_count):
            thread = QThread()
            worker = FaceScannerWorker(self.signals, i)
            worker.moveToThread(thread)
            
            thread.started.connect(worker.run)
            # We don't connect signals.finished to thread.quit immediately because other threads might be running.
            # Actually, standard behavior: running forever until stopped.
            
            # To clean up on stop:
            # We'll handle cleanup in stop_scan
            
            self.threads.append(thread)
            self.workers.append(worker)
            thread.start()
            
        self.signals.started.emit()

    @pyqtSlot()
    def stop_scan(self):
        # print("Stopping threads...")
        for worker in self.workers:
            worker.stop()
        
        # Wait for threads?
        # Ideally we wait.
        for thread in self.threads:
            thread.quit()
            thread.wait()
            
        self.threads = []
        self.workers = []
        self.signals.finished.emit()
