from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, 
    QGridLayout, QInputDialog, QMessageBox, QMenu, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSlot, QSize, QRect, QUrl
from PyQt6.QtGui import QPixmap, QPainter, QColor, QAction, QMouseEvent, QIcon, QPen, QPainterPath
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
        self.setMouseTracking(True)
        
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
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        # Card Background & Hover State
        rect = self.rect()
        bg_color = QColor("#222230") if self.is_hovered else QColor("#161622")
        border_color = QColor("#0078d4") if self.is_hovered else QColor("#2c2c3e")
        
        # Draw rounded card background
        painter.setBrush(bg_color)
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 12, 12)
        
        # Image Area
        img_rect = QRect(10, 10, 140, 140)
        
        # Paint background for image if not loaded
        painter.setBrush(QColor("#2d2d3d"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(img_rect, 8, 8)
        
        if self.pixmap:
            scaled = self.pixmap.scaled(img_rect.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            # Center crop with rounded corners
            path = QPainterPath()
            path.addRoundedRect(img_rect.x(), img_rect.y(), img_rect.width(), img_rect.height(), 8, 8)
            
            painter.save()
            painter.setClipPath(path)
            x = img_rect.x() + (img_rect.width() - scaled.width()) // 2
            y = img_rect.y() + (img_rect.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            painter.restore()
        else:
            # Draw placeholder icon/text (e.g. tag icon or initial)
            painter.setPen(QColor("#0078d4"))
            font = painter.font()
            font.setPointSize(28)
            font.setBold(True)
            painter.setFont(font)
            # Draw the first letter of the tag
            initial = self.tag_data['name'][0].upper() if self.tag_data['name'] else "#"
            painter.drawText(img_rect, Qt.AlignmentFlag.AlignCenter, initial)
            
        # Tag Name Text
        font = painter.font()
        font.setPointSize(11)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(QRect(10, 155, 140, 22), Qt.AlignmentFlag.AlignCenter, self.tag_data['name'])
        
        # Photos Count Text
        font.setBold(False)
        font.setPointSize(9)
        painter.setFont(font)
        painter.setPen(QColor("#9ca3af"))
        painter.drawText(QRect(10, 177, 140, 18), Qt.AlignmentFlag.AlignCenter, f"{self.tag_data['count']} Photos")

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

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(self.rename_tag_action)
        menu.addAction(rename_action)
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.delete_tag_action)
        menu.addAction(delete_action)
        
        menu.exec(event.globalPos())

    def rename_tag_action(self):
        old_name = self.tag_data['name']
        new_name, ok = QInputDialog.getText(self, "Rename Tag", "New tag name:", text=old_name)
        
        if ok and new_name:
            new_name = new_name.strip()
            # Basic validation
            if not new_name:
                return
            if new_name == old_name:
                return

            # Call model to rename
            tag_id = self.tag_data['id']
            self.gallery_model.rename_tag(tag_id, new_name)

    def delete_tag_action(self):
        tag_name = self.tag_data['name']
        tag_id = self.tag_data['id']
        
        confirm = QMessageBox.question(
            self,
            "Delete Tag",
            f"Are you sure you want to delete the tag '{tag_name}'? This will remove the tag from all associated photos.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            self.gallery_model.delete_tag(tag_id)

class CreateTagCard(QWidget):
    def __init__(self, on_click, parent=None):
        super().__init__(parent)
        self.on_click = on_click
        self.setFixedSize(160, 200)
        self.setMouseTracking(True)
        self.is_hovered = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        rect = self.rect()
        bg_color = QColor("#222230") if self.is_hovered else QColor("#161622")
        border_color = QColor("#0078d4") if self.is_hovered else QColor("#2c2c3e")
        
        # Draw rounded card background
        painter.setBrush(bg_color)
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 12, 12)
        
        # Image Area
        img_rect = QRect(10, 10, 140, 140)
        
        # Paint background for image
        painter.setBrush(QColor("#2d2d3d"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(img_rect, 8, 8)
        
        # Draw Plus Sign
        painter.setPen(QColor("#0078d4") if self.is_hovered else QColor("#9ca3af"))
        font = painter.font()
        font.setPointSize(48)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(img_rect, Qt.AlignmentFlag.AlignCenter, "+")
        
        # Tag Name Text
        font = painter.font()
        font.setPointSize(11)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(QRect(10, 155, 140, 22), Qt.AlignmentFlag.AlignCenter, "Create Tag")
        
        # Description/Helper text
        font.setBold(False)
        font.setPointSize(9)
        painter.setFont(font)
        painter.setPen(QColor("#71717a"))
        painter.drawText(QRect(10, 177, 140, 18), Qt.AlignmentFlag.AlignCenter, "Add a new tag")

    def enterEvent(self, event):
        self.is_hovered = True
        self.update()

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.on_click()

class TagsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gallery_model = GalleryModel.instance()
        self.thumbnail_generator = ThumbnailGenerator.instance()
        
        self.needs_refresh = True
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Title Label
        title_label = QLabel("Tags")
        title_label.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: bold; margin: 15px 15px 5px 15px;")
        self.layout.addWidget(title_label)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        self.content_widget = QWidget()
        self.flow_layout = FlowLayout(self.content_widget)
        
        self.scroll_area.setWidget(self.content_widget)
        self.layout.addWidget(self.scroll_area)
        
        # Connect Signals
        self.gallery_model.tagsChanged.connect(self.on_tags_changed)
        #self.thumbnail_generator.thumbnailReady.connect(self.on_thumbnail_ready)
        
        self.tag_cards = []

    def showEvent(self, event):
        super().showEvent(event)
        if self.needs_refresh:
            self.refresh_tags()

    def on_tags_changed(self):
        if self.isVisible():
            self.refresh_tags()
        else:
            self.needs_refresh = True

    def refresh_tags(self):
        self.needs_refresh = False
        # Clear
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
                item.widget().deleteLater()
        self.tag_cards = []
        
        # Get data
        tags_model = self.gallery_model.get_all_tags_model() # List of dicts
        
        for tag_data in tags_model:
            card = TagCard(tag_data, self.on_tag_clicked)
            self.flow_layout.addWidget(card)
            self.tag_cards.append(card)

        # Add the Create Tag Card at the end
        create_card = CreateTagCard(self.create_new_tag)
        self.flow_layout.addWidget(create_card)
        self.tag_cards.append(create_card)

    def on_tag_clicked(self, tag_name):
        self.gallery_model.set_tag_filter(tag_name)
        # Use model signal for navigation
        self.gallery_model.request_switch_to_gallery()

    @pyqtSlot(str, str)
    def on_thumbnail_ready(self, file_path, thumb_path):
        for card in self.tag_cards:
            if card.tag_data['coverPath'] == file_path:
                card.set_thumbnail(thumb_path)

    def create_new_tag(self):
        name, ok = QInputDialog.getText(self, "Create New Tag", "New Tag name:")
        if ok and name:
            name = name.strip()
            if name:
                self.gallery_model.add_new_tag(name)
