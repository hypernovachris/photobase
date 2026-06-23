from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtCore import Qt, QRect, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap, QFont
from core.gallery_model import GalleryModel
from core.thumbnail_generator import ThumbnailGenerator
from collections import OrderedDict
import os

class LRUCache:
    def __init__(self, maxsize=1000):
        self.cache = OrderedDict()
        self.maxsize = maxsize

    def get(self, key, default=None):
        if key not in self.cache:
            return default
        self.cache.move_to_end(key)
        return self.cache[key]

    def set(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.maxsize:
            self.cache.popitem(last=False)

    def pop(self, key, default=None):
        return self.cache.pop(key, default)

    def __contains__(self, key):
        return key in self.cache

    def clear_failures(self):
        # Remove False entries so they can be re-evaluated
        keys_to_remove = [k for k, v in self.cache.items() if v is False]
        for k in keys_to_remove:
            self.cache.pop(k, None)

    def clear(self):
        self.cache.clear()

class GalleryItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gallery_model = GalleryModel.instance()
        self.thumbnail_generator = ThumbnailGenerator.instance()
        self.thumb_cache = LRUCache(maxsize=1000) # path -> QPixmap cache to speed up rendering with LRU eviction

    def sizeHint(self, option, index):
        item = index.data(Qt.ItemDataRole.UserRole)
        if item and item.get("type") == "header":
            return QSize(option.rect.width(), 50)
        return QSize(option.rect.width(), 138)

    def paint(self, painter, option, index):
        item = index.data(Qt.ItemDataRole.UserRole)
        if not item:
            return
            
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        
        if item.get("type") == "header":
            # Paint Header
            month_text = item.get("month_text", "")
            painter.setPen(QColor("#e4e4e7"))
            font = painter.font()
            font.setBold(True)
            font.setPointSize(14)
            painter.setFont(font)
            
            # Position text slightly offset
            text_rect = option.rect.adjusted(10, 10, -10, -10)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, month_text)
            
        elif item.get("type") == "images":
            images = item.get("images", [])
            col_width = 138 # 128 thumbnail + 10 spacing
            
            for col, img in enumerate(images):
                path = img["path"]
                thumb_path = img["thumbnailPath"]
                
                # Rect of the thumbnail cell
                x = option.rect.x() + col * col_width + 5
                y = option.rect.y() + 5
                rect = QRect(x, y, 128, 128)
                
                is_selected = self.gallery_model.is_selected(path)
                
                # Retrieve from cache
                pixmap_or_status = self.thumb_cache.get(path)
                if pixmap_or_status is not None:
                    if isinstance(pixmap_or_status, QPixmap):
                        painter.drawPixmap(rect, pixmap_or_status)
                    else:
                        # False: doesn't exist yet
                        painter.fillRect(rect, QColor("#333333"))
                else:
                    if os.path.exists(thumb_path):
                        pixmap = QPixmap(thumb_path)
                        if not pixmap.isNull():
                            self.thumb_cache.set(path, pixmap)
                            painter.drawPixmap(rect, pixmap)
                        else:
                            self.thumb_cache.set(path, False)
                            painter.fillRect(rect, QColor("#333333"))
                    else:
                        # Doesn't exist, request it
                        self.thumb_cache.set(path, False)
                        painter.fillRect(rect, QColor("#333333"))
                        self.thumbnail_generator.request_thumbnail(path)
                        
                # Draw Selection outline
                if is_selected:
                    pen = QPen(QColor(0, 120, 215)) # Windows blue
                    pen.setWidth(4)
                    painter.setPen(pen)
                    painter.drawRect(rect.adjusted(2, 2, -2, -2))
                    
        painter.restore()
