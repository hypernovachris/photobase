from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, 
    QGridLayout, QInputDialog, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, pyqtSlot, QSize, QRect, QUrl
from PyQt6.QtGui import QPixmap, QPainter, QColor, QAction, QMouseEvent, QIcon
from ui.widgets.util.flow_layout import FlowLayout
import os
from core.thumbnail_generator import ThumbnailGenerator
from core.gallery_model import GalleryModel

class TagCard(QWidget):
    def __init__(self, tag_data, on_click, parent=None):
        super().__init__(parent)
        self.tag_data = tag_data # {id, name, count, thumbnail, coverPath}
        self.gallery_model = GalleryModel.instance()
        self.thumbnail_generator = ThumbnailGenerator.instance()
        self.on_click = on_click
        
        self.setFixedSize(160, 200)
        
        self.is_hovered = False
        self.pixmap = None
        
        # Load thumbnail
        # self.tag_data['thumbnail'] is a QUrl string from model
        thumb_url = self.tag_data.get('thumbnail', "")
        cover_path = self.tag_data.get('coverPath', "")
        
        if thumb_url:
             # Try to load formatted thumbnail
             local_path = QUrl(thumb_url).toLocalFile()
             if os.path.exists(local_path):
                 self.pixmap = QPixmap(local_path)
             elif cover_path and os.path.exists(cover_path):
                 # Fallback to requesting generation
                 self.thumbnail_generator.request_thumbnail(cover_path)
        elif cover_path and os.path.exists(cover_path):
             self.thumbnail_generator.request_thumbnail(cover_path)

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Card Background
        # painter.drawRect(0, 0, self.width(), self.height())
        
        # Image Area
        img_rect = QRect(10, 10, 140, 140)
        # painter.drawRect(img_rect)
        
        if self.pixmap:
            scaled = self.pixmap.scaled(img_rect.size(), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
            # Center crop
            x = img_rect.x() + (img_rect.width() - scaled.width()) // 2
            y = img_rect.y() + (img_rect.height() - scaled.height()) // 2
            painter.setClipRect(img_rect)
            painter.drawPixmap(x, y, scaled)
            painter.setClipping(False)
            
        # Text
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRect(10, 160, 140, 20), Qt.AlignmentFlag.AlignCenter, self.tag_data['name'])
        
        font.setBold(False)
        painter.setFont(font)
        painter.drawText(QRect(10, 180, 140, 20), Qt.AlignmentFlag.AlignCenter, f"{self.tag_data['count']} Photos")

    def enterEvent(self, event):
        self.is_hovered = True
        self.update()

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.on_click(self.tag_data['name'])

    def set_thumbnail(self, path):
        if os.path.exists(path):
            self.pixmap = QPixmap(path)
            self.update()

class TagsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gallery_model = GalleryModel.instance()
        self.thumbnail_generator = ThumbnailGenerator.instance()
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        self.content_widget = QWidget()
        self.flow_layout = FlowLayout(self.content_widget)
        
        self.scroll_area.setWidget(self.content_widget)
        self.layout.addWidget(self.scroll_area)
        
        # Connect Signals
        self.gallery_model.tagsChanged.connect(self.refresh_tags)
        #self.thumbnail_generator.thumbnailReady.connect(self.on_thumbnail_ready)
        
        self.tag_cards = []
        self.refresh_tags()

    def refresh_tags(self):
        # Clear
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.tag_cards = []
        
        # Get data
        tags_model = self.gallery_model.get_all_tags_model() # List of dicts
        
        for tag_data in tags_model:
            card = TagCard(tag_data, self.on_tag_clicked)
            self.flow_layout.addWidget(card)
            self.tag_cards.append(card)

    def on_tag_clicked(self, tag_name):
        self.gallery_model.set_tag_filter(tag_name)
        # Use model signal for navigation
        self.gallery_model.request_switch_to_gallery()

    @pyqtSlot(str, str)
    def on_thumbnail_ready(self, file_path, thumb_path):
        for card in self.tag_cards:
            if card.tag_data['coverPath'] == file_path:
                card.set_thumbnail(thumb_path)
