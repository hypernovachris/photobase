from PyQt6.QtCore import QAbstractListModel, Qt, QVariant, QModelIndex, QUrl, pyqtSlot
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

    def load_images(self):
        self.beginResetModel()
        self._sections = []
        db.connect()
        
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
