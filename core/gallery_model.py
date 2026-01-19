from PyQt6.QtCore import QAbstractListModel, Qt, QVariant, QModelIndex, QUrl, pyqtSlot, pyqtSignal, pyqtProperty
from core.database import db
import os
from PIL import Image

def month_numericstr_to_text(numeric_month_str):
    if not numeric_month_str:
        return ""
    try:
        parts = numeric_month_str.split('-')
        if len(parts) != 2:
            return numeric_month_str
        year_str, month_num = parts
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        month_str = months[int(month_num) - 1]
        return month_str + " " + year_str
    except ValueError:
        return numeric_month_str

class GalleryModel(QAbstractListModel):
    MonthTextRole = Qt.ItemDataRole.UserRole + 1
    ImagesRole = Qt.ItemDataRole.UserRole + 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sections = []
        self._active_filters = []
        # Support legacy properties for active filter display
        self._active_filter_name = ""

        self.load_images()

    def roleNames(self):
        return {
            GalleryModel.MonthTextRole: b"monthText",
            GalleryModel.ImagesRole: b"images"
        }

    def rowCount(self, parent=QModelIndex()):
        return len(self._sections)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._sections)):
            return QVariant()
        
        section = self._sections[index.row()]
        
        if role == GalleryModel.MonthTextRole:
            return section['month_text']
        elif role == GalleryModel.ImagesRole:
            return section['images']
            
        return QVariant()
    
    @pyqtSlot(int, result=int)
    def getImageCountForMonth(self, monthIndex):
        if 0 <= monthIndex < len(self._sections):
            return len(self._sections[monthIndex]['images'])
        return 0
    
    @pyqtSlot()
    def refresh(self):
        self.load_images()
        self.tagsChanged.emit()

    def load_images(self):
        self.beginResetModel()
        self._sections = []
        db.connect()
        
        # 1. Get Distinct Months based on current filter
        month_strings = db.images.get_filtered_months(self._active_filters)
        
        for month_str in month_strings:
            # 2. Get Images for Month based on current filter
            image_rows = db.images.get_filtered_images(month_str, self._active_filters)
            
            image_list = []
            for (file_path, thumb_path) in image_rows:
                abs_thumb_path = os.path.abspath(thumb_path)
                image_list.append({
                    'path': file_path,
                    'thumbnail': QUrl.fromLocalFile(abs_thumb_path).toString()
                })
                
            self._sections.append({
                'month_text': month_numericstr_to_text(month_str),
                'images': image_list
            })
            
        db.close()
        self.endResetModel()
        self.countChanged.emit()

    countChanged = pyqtSignal()

    @pyqtProperty(int, notify=countChanged)
    def count(self):
        return self.rowCount()

    # --- Selection Handling ---

    _selected_paths = set()
    last_selected_path = None # For Shift+Click range

    selectionChanged = pyqtSignal(list, arguments=['selectedPaths'])

    @pyqtSlot(str, int)
    def handle_selection(self, path, modifiers):
        
        ctrl_pressed = (modifiers & Qt.KeyboardModifier.ControlModifier.value)
        shift_pressed = (modifiers & Qt.KeyboardModifier.ShiftModifier.value)
        
        # Use Python set for internal logic
        new_selection = set(self._selected_paths)
        
        if shift_pressed and self.last_selected_path and self.last_selected_path != path:
            # Range Selection
            start_path = self.last_selected_path
            end_path = path
            
            # Find coordinates
            start_pos = self._find_path_coordinates(start_path)
            end_pos = self._find_path_coordinates(end_path)
            
            if start_pos and end_pos:
                # Traverse range
                range_paths = self._get_paths_in_range(start_pos, end_pos)
                
                if not ctrl_pressed:
                    new_selection.clear()
                    
                for p in range_paths:
                    new_selection.add(p)
        
        elif ctrl_pressed:
            # Toggle Selection
            if path in new_selection:
                new_selection.remove(path)
            else:
                new_selection.add(path)
                self.last_selected_path = path
        else:
            # Single Click (Replace)
            new_selection.clear()
            new_selection.add(path)
            self.last_selected_path = path

        self._update_selection(new_selection)

    def _update_selection(self, new_selection_set):
        if self._selected_paths != new_selection_set:
            self._selected_paths = new_selection_set
            self.selectionChanged.emit(list(self._selected_paths))

    @pyqtSlot(str, result=bool)
    def is_selected(self, path):
        return path in self._selected_paths

    @pyqtSlot(result=list)
    def get_selected_paths(self):
        return list(self._selected_paths)

    @pyqtSlot(str)
    def open_file(self, path):
        if os.path.exists(path):
            os.startfile(path)

    @pyqtSlot(str)
    def reveal_file(self, path):
        if os.path.exists(path):
            # Windows specific explorer selection
            # TODO: cross platform
            import subprocess
            subprocess.Popen(['explorer', '/select,', os.path.normpath(path)])

    def _find_path_coordinates(self, path):
        # Returns (section_index, image_index)
        for s_idx, section in enumerate(self._sections):
            for i_idx, img in enumerate(section['images']):
                if img['path'] == path:
                    return (s_idx, i_idx)
        return None

    def _get_paths_in_range(self, pos1, pos2):
        # Order inputs
        s1, i1 = pos1
        s2, i2 = pos2
        
        if s1 > s2 or (s1 == s2 and i1 > i2):
            s1, i1, s2, i2 = s2, i2, s1, i1
            
        collected = []
        in_range = False
        
        for s_idx in range(s1, s2 + 1):
            section = self._sections[s_idx]
            images = section['images']
            
            start_i = i1 if s_idx == s1 else 0
            end_i = i2 if s_idx == s2 else len(images) - 1
            
            for i in range(start_i, end_i + 1):
                collected.append(images[i]['path'])
                
        return collected
        return collected

    # --- Tagging Integration ---
    
    tagsChanged = pyqtSignal()

    @pyqtSlot(str, result=bool)
    def add_new_tag(self, tag_name):
        db.connect()
        tag_id = db.tags.get_or_create_tag(tag_name)
        db.commit() # Ensure it is saved
        db.close()
        if tag_id:
            self.tagsChanged.emit()
        return tag_id is not None

    @pyqtSlot(str)
    def apply_tag_to_selection(self, tag_name):
        if not self._selected_paths:
            return
            
        db.connect()
        tag_id = db.tags.get_or_create_tag(tag_name)
        if tag_id:
            for path in self._selected_paths:
                img_id = db.images.get_image_id(path)
                if img_id:
                    db.tags.add_tag_to_image(img_id, tag_id)
            db.commit()
            self.tagsChanged.emit()
        db.close()

    @pyqtSlot()
    def remove_selection_from_active_filter(self):
        if not self._selected_paths:
            return
            
        db.connect()

        # Iterate over all active filters
        for f in self._active_filters:
             ftype = f.get('type')
             val = f.get('value')
                 
             if ftype == 'tag':
                 # val is tag_name
                 # need tag_id
                 tag_id = db.tags.get_or_create_tag(val)
                 if tag_id:
                     for path in self._selected_paths:
                         img_id = db.images.get_image_id(path)
                         if img_id:
                             db.tags.remove_tag_from_image(img_id, tag_id)
                 self.tagsChanged.emit()

        db.commit()
        # Refresh the view because items might no longer belong to the filter
        self.load_images() 
        db.close()

    @pyqtSlot(str)
    def remove_tag_from_selection(self, tag_name):
        # Keep for backward compatibility or direct calls
        if not self._selected_paths:
            return
            
        db.connect()

        tag_id = db.tags.get_or_create_tag(tag_name) 
        
        if tag_id:
            for path in self._selected_paths:
                img_id = db.images.get_image_id(path)
                if img_id:
                    db.tags.remove_tag_from_image(img_id, tag_id)
            db.commit()
            self.tagsChanged.emit()
        db.close()

    @pyqtSlot(result=list)
    def get_all_tags_list(self):
        db.connect()
        tags = db.tags.get_all_tags() # returns list of (id, name)
        db.close()
        return [t[1] for t in tags]

    @pyqtSlot(result=list)
    def get_all_cameras(self):
        db.connect()
        res = db.images.get_all_cameras()
        db.close()
        return res

    @pyqtSlot(result=list)
    def get_all_lenses(self):
        db.connect()
        res = db.images.get_all_lenses()
        db.close()
        return res

    @pyqtSlot(result=list)
    def get_all_tags_model(self):
        """Returns a list of dictionaries for QML: name, count, thumbnail"""
        db.connect()
        # Returns [(name, count, cover_path, cover_thumb_path), ...]
        rows = db.tags.get_tags_with_metadata()
        db.close()
        
        result = []
        for row in rows:
            tag_id, name, count, cover_path, cover_thumb_path = row
            thumb_url = ""
            
            # If we have a thumbnail path, verify it exists and convert to QUrl
            if cover_thumb_path and os.path.exists(cover_thumb_path):
                thumb_url = QUrl.fromLocalFile(os.path.abspath(cover_thumb_path)).toString()
            elif cover_path and os.path.exists(cover_path):
                thumb_url = QUrl.fromLocalFile(os.path.abspath(cover_path)).toString()
            
            result.append({
                "id": tag_id,
                "name": name,
                "count": count,
                "thumbnail": thumb_url,
                "coverPath": cover_path # For triggering generation if needed
            })
        return result



    # --- Filtering ---
    
    filterChanged = pyqtSignal(str, arguments=['tagName'])

    @pyqtSlot(str)
    def set_tag_filter(self, tag_name):
        self._active_filters = [{'type': 'tag', 'value': tag_name}]
        self._active_filter_name = tag_name
        self.load_images()
        self.filterChanged.emit(tag_name)
    
    @pyqtSlot()
    def clear_tag_filter(self):
        self._active_filters = []
        self._active_filter_name = ""
        self.load_images()
        self.filterChanged.emit("")
        
    @pyqtSlot(list)
    def search(self, filters):
        self._active_filters = filters
        self._active_filter_name = "Search Results"
        self.load_images()
        self.filterChanged.emit("Search Results")

    @pyqtSlot(int, str)
    def rename_tag(self, tag_id, new_name):
        db.connect()
        success = db.tags.rename_tag(tag_id, new_name)
        if success:
            db.commit()
            self.tagsChanged.emit()
        db.close()
        
    @pyqtSlot(result=str)
    def get_active_filter(self):
        return self._active_filter_name
    
    def _get_formatted_file_size(self, file_path):
        try:
            size_bytes = os.path.getsize(file_path)
            units = ["B", "KB", "MB", "GB"]
            size = float(size_bytes)
            unit_index = 0
            while size >= 1024 and unit_index < len(units) - 1:
                size /= 1024
                unit_index += 1
            
            if unit_index == 0:
                return f"{int(size)} {units[unit_index]}"
            else:
                return f"{size:.1f} {units[unit_index]}"
        except OSError:
            return "Unavailable"

    def _get_formatted_image_size(self, file_path):
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                megapixels = (width * height) / 1_000_000
                return f"{megapixels:.1f} MP ({width}x{height})"
        except Exception:
            return "Unavailable"

    @pyqtSlot(str, result=QVariant)
    def get_image_details(self, file_path):
        if not file_path or not os.path.exists(file_path):
            return None
            
        import datetime
        dt = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
        date_str = dt.strftime("%B %d, %Y, %I:%M %p")
        
        from core.image_processing import get_exif_string
        
        db.connect()
        img_id = db.images.get_image_id(file_path)
        
        camera = "Unavailable"
        lens = "Unavailable"
        
        meta = db.images.get_image_metadata(file_path)
        if meta:
            if meta[0]: camera = meta[0]
            if meta[1]: lens = meta[1]

        tags = []
        if img_id:
            tags = [t[1] for t in db.tags.get_tags_for_image(img_id)]
        db.close()
        
        return {
            "date": date_str,
            "tags": tags,
            "exifString": get_exif_string(file_path),
            "camera": camera,
            "lens": lens,
            "fileSize": self._get_formatted_file_size(file_path),
            "imageSize": self._get_formatted_image_size(file_path)
        }


    @pyqtSlot(str, result=str)
    def get_image_url(self, file_path):
        if not file_path:
            print("No file path provided")
            return ""
        
        # Check for HEIC
        lower_path = file_path.lower()
        if lower_path.endswith('.heic') or lower_path.endswith('.heif'):
            # Use QUrl to ensure proper encoding of special characters (like #)
            url = QUrl.fromLocalFile(file_path)
            url.setScheme("image")
            url.setHost("heic")
            return url.toString()
            
        return QUrl.fromLocalFile(file_path).toString()

    @pyqtSlot(str, result=str)
    def get_next_image_path(self, current_path):
        coords = self._find_path_coordinates(current_path)
        if not coords:
            return ""
        
        s_idx, i_idx = coords
        section = self._sections[s_idx]
        images = section['images']
        
        # Try next image in current section
        if i_idx + 1 < len(images):
             return images[i_idx + 1]['path']
        
        # Try first image of next section
        if s_idx + 1 < len(self._sections):
             next_section = self._sections[s_idx + 1]
             if next_section['images']:
                 return next_section['images'][0]['path']
                 
        return ""

    @pyqtSlot(str, result=str)
    def get_previous_image_path(self, current_path):
        coords = self._find_path_coordinates(current_path)
        if not coords:
            return ""
        
        s_idx, i_idx = coords
        
        # Try previous image in current section
        if i_idx - 1 >= 0:
            section = self._sections[s_idx]
            return section['images'][i_idx - 1]['path']
            
        # Try last image of previous section
        if s_idx - 1 >= 0:
            prev_section = self._sections[s_idx - 1]
            if prev_section['images']:
                return prev_section['images'][-1]['path']
                
        return ""

    @pyqtSlot(str, str)
    def add_tag_to_image_path(self, file_path, tag_name):
        db.connect()
        img_id = db.images.get_image_id(file_path)
        tag_id = db.tags.get_or_create_tag(tag_name)
        if img_id and tag_id:
             db.tags.add_tag_to_image(img_id, tag_id)
             db.commit()
             self.tagsChanged.emit()
        db.close()

    @pyqtSlot(str, str)
    def remove_tag_from_image_path(self, file_path, tag_name):
        db.connect()
        img_id = db.images.get_image_id(file_path)
        # We need tag id
        # get_or_create is safe? Yes, if it exists we get ID. If not created, we get ID.
        # If we remove a tag that doesn't exist, nothing happens.
        tag_id = db.tags.get_or_create_tag(tag_name)
        if img_id and tag_id:
             db.tags.remove_tag_from_image(img_id, tag_id)
             db.commit()
             self.tagsChanged.emit()
        db.close()
