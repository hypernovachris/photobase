from PyQt6.QtCore import QAbstractListModel, Qt, QVariant, QModelIndex, QUrl, pyqtSlot, pyqtSignal
from core.database import db
import os

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
        self._filter_tag_id = None
        self._filter_tag_name = None
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
    
    @pyqtSlot()
    def refresh(self):
        self.load_images()
        self.tagsChanged.emit()

    def load_images(self):
        self.beginResetModel()
        self._sections = []
        db.connect()
        
        # Base query parts
        if self._filter_tag_id is not None:
             # Filtered query
             # 1. Get Distinct Months for images with tag
            db.cursor.execute("""
                SELECT DISTINCT strftime('%Y-%m', datetime(i.last_modified, 'unixepoch')) AS month 
                FROM images i
                JOIN image_tags it ON i.id = it.image_id
                WHERE it.tag_id = ?
                ORDER BY month DESC;
            """, (self._filter_tag_id,))
            month_rows = db.cursor.fetchall()
            
            for (month_str,) in month_rows:
                # 2. Get Images for Month with tag
                db.cursor.execute("""
                    SELECT i.file_path, i.thumbnail_path 
                    FROM images i
                    JOIN image_tags it ON i.id = it.image_id
                    WHERE it.tag_id = ? 
                    AND strftime('%Y-%m', datetime(i.last_modified, 'unixepoch')) = ?
                    ORDER BY i.last_modified DESC
                """, (self._filter_tag_id, month_str))
                
                image_rows = db.cursor.fetchall()
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

        else:
            # Original Unfiltered Logic
            # 1. Get Distinct Months
            db.cursor.execute("SELECT DISTINCT strftime('%Y-%m', datetime(last_modified, 'unixepoch')) AS month FROM images ORDER BY month DESC;")
            month_rows = db.cursor.fetchall()
            
            for (month_str,) in month_rows:
                # 2. Get Images for Month
                db.cursor.execute("""
                    SELECT file_path, thumbnail_path 
                    FROM images
                    WHERE strftime('%Y-%m', datetime(last_modified, 'unixepoch')) = ?
                    ORDER BY last_modified DESC
                """, (month_str,))
                
                image_rows = db.cursor.fetchall()
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

    # --- Selection Handling ---

    _selected_paths = set()
    last_selected_path = None # For Shift+Click range

    selectionChanged = pyqtSignal(list, arguments=['selectedPaths'])

    @pyqtSlot(str, int)
    def handle_selection(self, path, modifiers):
        """
        modifiers: Qt.KeyboardModifiers flags (as int)
        Qt.ControlModifier = 0x04000000 (roughly, but we can just check if it's non-zero/specific bit)
        Actually from QML it might send the enum value.
        Qt.ShiftModifier = 0x02000000
        Qt.ControlModifier = 0x04000000
        """
        
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
                
                # If CTRL is NOT pressed, clear previous first (standard behavior often behaves like this, 
                # but standard file explorer usually extends selection. 
                # Requirements said: "Holding Shift ... selects every thumbnail between it and the last selected"
                # Usually standard behavior:
                # Click A. Shift+Click B -> Selects A..B. 
                # Click A. Click C. Shift+Click B -> Selects C..B (clears A usually, unless Ctrl held?)
                # Win Explorer: Click A. Shift+Click B -> A..B selected.
                # Let's assume Shift+Click REPLACES selection with the range, unless Ctrl is also held?
                # Actually user requirement: "Holding Shift while clicking a thumbnail selects every thumbnail between it and the last selected thumbnail (inclusive)"
                # Implicitly, does it keep others? 
                # Let's stick to: If Ctrl is NOT held, we normally clear selection first in a simple explorer.
                # But "adds it" was specific for Ctrl. 
                # I will implement: Shift+Click adds the range. If they want to clear, they click without modifiers first.
                # Actually, usually Shift+Click starts a NEW selection range anchored at the 'current' item.
                # Let's just Clear then Select Range if Ctrl is not pressed, similar to single click.
                
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
        tag_id = db.get_or_create_tag(tag_name)
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
        tag_id = db.get_or_create_tag(tag_name)
        if tag_id:
            for path in self._selected_paths:
                img_id = db.get_image_id(path)
                if img_id:
                    db.add_tag_to_image(img_id, tag_id)
            db.commit()
            self.tagsChanged.emit()
        db.close()

    @pyqtSlot(str)
    def remove_tag_from_selection(self, tag_name):
        if not self._selected_paths:
            return
            
        db.connect()
        # resolving id from name first
        # Ideally we should pass IDs but UI might send names.
        # Let's get ID.
        # But wait, we don't have get_tag_id_by_name exposed but get_or_create does return ID.
        # We shouldn't create if we are removing though.
        # Let's use get_or_create for now or add a helper.
        # Actually, if we use get_or_create it's fine, if it didn't exist it wouldn't be on the image.
        tag_id = db.get_or_create_tag(tag_name) 
        
        if tag_id:
            for path in self._selected_paths:
                img_id = db.get_image_id(path)
                if img_id:
                    db.remove_tag_from_image(img_id, tag_id)
            db.commit()
            self.tagsChanged.emit()
        db.close()

    @pyqtSlot(result=list)
    def get_all_tags_list(self):
        db.connect()
        tags = db.get_all_tags() # returns list of (id, name)
        db.close()
        return [t[1] for t in tags]

    @pyqtSlot(result=list)
    def get_all_tags_model(self):
        """Returns a list of dictionaries for QML: name, count, thumbnail"""
        db.connect()
        # Returns [(name, count, cover_path, cover_thumb_path), ...]
        rows = db.get_tags_with_metadata()
        db.close()
        
        result = []
        for row in rows:
            name, count, cover_path, cover_thumb_path = row
            thumb_url = ""
            
            # If we have a thumbnail path, verify it exists and convert to QUrl
            if cover_thumb_path and os.path.exists(cover_thumb_path):
                thumb_url = QUrl.fromLocalFile(os.path.abspath(cover_thumb_path)).toString()
            elif cover_path and os.path.exists(cover_path):
                 # Fallback to full image if thumbnail missing (though main view generaates them)
                 # Or just leave empty and let UI handle placeholder?
                 # Assuming if cover_path exists, we might want to trigger generation or show it.
                 # Let's show it.
                 thumb_url = QUrl.fromLocalFile(os.path.abspath(cover_path)).toString()
            
            result.append({
                "name": name,
                "count": count,
                "thumbnail": thumb_url,
                "coverPath": cover_path # For triggering generation if needed
            })
        return result

    @pyqtSlot(result=list)
    def get_common_tags(self):
        if not self._selected_paths:
            return []
            
        db.connect()
        # Resolve all paths to IDs
        img_ids = []
        for path in self._selected_paths:
            iid = db.get_image_id(path)
            if iid:
                img_ids.append(iid)
                
        if not img_ids:
            db.close()
            return []
            
        common_tags = db.get_common_tags_for_images(img_ids)
        db.close()
        return [t[1] for t in common_tags]

    # --- Filtering ---
    
    filterChanged = pyqtSignal(str, arguments=['tagName'])

    @pyqtSlot(str)
    def set_tag_filter(self, tag_name):
        try:
            db.connect()
            # Find ID
            db.cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
            res = db.cursor.fetchone()
            db.close()
            
            if res:
                self._filter_tag_id = res[0]
                self._filter_tag_name = tag_name
                self.load_images()
                self.filterChanged.emit(tag_name)
        except Exception as e:
            print(f"Error setting filter: {e}")
            if db.connection:
                db.close()
    
    @pyqtSlot()
    def clear_tag_filter(self):
        self._filter_tag_id = None
        self._filter_tag_name = None
        self.load_images()
        self.filterChanged.emit("")
        
    @pyqtSlot(result=str)
    def get_active_filter(self):
        return self._filter_tag_name if self._filter_tag_name else ""

