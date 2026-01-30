from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, QMenu, QApplication, QHBoxLayout, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSlot, QSize, QRect, QTimer, QPoint
from PyQt6.QtGui import QPixmap, QPainter, QColor, QAction, QMouseEvent
from core.theme import Theme
from ui.widgets.flow_layout import FlowLayout
import os

class ThumbnailWidget(QWidget):
    def __init__(self, file_path, gallery_model, thumbnail_generator, gallery_view, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.gallery_model = gallery_model
        self.thumbnail_generator = thumbnail_generator
        self.gallery_view = gallery_view
        
        self.setFixedSize(128, 128)
        self.pixmap = None
        self.is_selected = False
        self.is_loaded = False
        self.setMouseTracking(True)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Draw Background
        painter.fillRect(self.rect(), Theme.buttonColor)
        
        # Draw Image
        if self.pixmap:
            # Aspect Ratio Crop (Center)
            # Scaling logic similar to QML's Image.PreserveAspectCrop
            img_size = self.pixmap.size()
            widget_size = self.size()
            
            scaled = self.pixmap.scaled(widget_size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            
            # Center crop
            x = (scaled.width() - widget_size.width()) // 2
            y = (scaled.height() - widget_size.height()) // 2
            
            painter.drawPixmap(0, 0, scaled, x, y, widget_size.width(), widget_size.height())
        
        # Draw Selection Overlay
        if self.is_selected:
            pen = painter.pen()
            pen.setColor(Theme.highlightColor)
            pen.setWidth(4)
            painter.setPen(pen)
            painter.drawRect(2, 2, self.width()-4, self.height()-4)
            
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            # Pass modifiers as integer to match GalleryModel expectation
            modifiers = int(event.modifiers().value)
            self.gallery_model.handle_selection(self.file_path, modifiers)
        elif event.button() == Qt.MouseButton.RightButton:
            if not self.is_selected:
                self.gallery_model.handle_selection(self.file_path, 0)
            # Context menu handled in contextMenuEvent
            
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        
        open_action = QAction("Open", self)
        open_action.triggered.connect(lambda: self.gallery_view.open_image(self.file_path))
        menu.addAction(open_action)
        
        reveal_action = QAction("Reveal in File Explorer", self)
        reveal_action.triggered.connect(lambda: self.gallery_model.reveal_file(self.file_path))
        menu.addAction(reveal_action)
        
        # Add Tag / Edit Tags
        edit_tags_action = QAction("Edit Tags", self)
        from ui.widgets.tag_edit_dialog import TagEditDialog
        # Determine if we are editing single or multi
        selected = self.gallery_model.get_selected_paths()
        target = "" # Default multi
        if len(selected) <= 1:
            target = self.file_path
        
        edit_tags_action.triggered.connect(lambda: self.open_tag_dialog(target))
        menu.addAction(edit_tags_action)
        
        menu.exec(event.globalPos())

    def open_tag_dialog(self, target):
        from ui.widgets.tag_edit_dialog import TagEditDialog
        dialog = TagEditDialog(self.gallery_model, target_path=target, parent=self)
        dialog.exec()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.gallery_view.open_image(self.file_path)

    def set_selected(self, selected):
        if self.is_selected != selected:
            self.is_selected = selected
            self.update()

    def load_thumbnail(self):
        if self.is_loaded:
            return
        # Display cached if available or request
        # self.thumbnail_generator.request_thumbnail handles check
        self.thumbnail_generator.request_thumbnail(self.file_path)

    def set_thumbnail(self, path):
        if os.path.exists(path):
            self.pixmap = QPixmap(path)
            self.is_loaded = True
            self.update()

class MonthWidget(QWidget):
    def __init__(self, month_text, images, gallery_model, thumbnail_generator, gallery_view, parent=None):
        super().__init__(parent)
        self.gallery_model = gallery_model
        self.thumbnail_generator = thumbnail_generator
        self.gallery_view = gallery_view
        self.image_widgets = []
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QLabel(month_text)
        header.setStyleSheet(f"font-size: {Theme.fontSizeSubheader}px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Flow
        self.flow_widget = QWidget()
        self.flow_layout = FlowLayout(self.flow_widget)
        self.flow_layout.setSpacing(Theme.spacingMedium)
        
        for img_data in images:
            path = img_data['path']
            tw = ThumbnailWidget(path, gallery_model, thumbnail_generator, gallery_view)
            self.flow_layout.addWidget(tw)
            self.image_widgets.append(tw)
            
        layout.addWidget(self.flow_widget)

class GalleryView(QWidget):
    def __init__(self, gallery_model, thumbnail_generator, parent=None):
        super().__init__(parent)
        self.gallery_model = gallery_model
        self.thumbnail_generator = thumbnail_generator
        
        
        # self.image_viewer = ImageViewer(self.gallery_model) # Now handled by MainWindow via open_image delegation
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setContentsMargins(0, 0, 0, 0)
        
        # Filter Banner
        self.filter_banner = QWidget()
        self.filter_banner.setStyleSheet(f"background-color: {Theme.secondaryBackgroundColor.name()}; border-bottom: 1px solid {Theme.borderColor.name()};")
        self.filter_banner.hide()
        
        banner_layout = QHBoxLayout(self.filter_banner)
        banner_layout.setContentsMargins(10, 5, 10, 5)
        
        self.filter_label = QLabel("Filter Active")
        self.filter_label.setStyleSheet(f"color: {Theme.textColor.name()}; font-weight: bold;")
        banner_layout.addWidget(self.filter_label)
        
        banner_layout.addStretch()
        
        clear_btn = QPushButton("Clear Filter")
        clear_btn.setStyleSheet(f"color: {Theme.highlightColor.name()}; border: 1px solid {Theme.highlightColor.name()}; padding: 4px 8px; border-radius: 4px;")
        clear_btn.clicked.connect(self.gallery_model.clear_filter)
        banner_layout.addWidget(clear_btn)
        
        self.layout.addWidget(self.filter_banner)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(Theme.spacingLarge)
        
        self.scroll_area.setWidget(self.content_widget)
        self.layout.addWidget(self.scroll_area)
        
        # Connect Signals
        self.gallery_model.countChanged.connect(self.reload_view)
        # self.gallery_model.filterChanged.connect(self.reload_view) # Reload triggers content reset
        self.gallery_model.filterChanged.connect(self.on_filter_changed)
        self.gallery_model.selectionChanged.connect(self.update_selection)
        self.thumbnail_generator.thumbnailReady.connect(self.on_thumbnail_ready)
        
        # Scroll Visibility Check
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.check_visibility)
        
        # Delayed check for initial load
        QTimer.singleShot(100, self.check_visibility)
        
        # Initial Load
        self.reload_view()

    @pyqtSlot(str)
    def open_image(self, path):
        # Use model signal to request open image
        self.gallery_model.request_open_image(path)

    @pyqtSlot()
    def on_filter_changed(self):
        # Update Banner
        active_filters = self.gallery_model.active_filters
        if active_filters:
            self.filter_banner.show()
            # self.filter_label.setText(f"Filter Active: {len(active_filters)} criteria")
        else:
            self.filter_banner.hide()
        
        # self.reload_view() # Redundant: handled by countChanged via load_images

    @pyqtSlot()
    def reload_view(self):
        # Clear existing
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.all_thumb_widgets = []
        
        count = self.gallery_model.rowCount()
        for i in range(count):
            idx = self.gallery_model.index(i, 0)
            month_text = self.gallery_model.data(idx, self.gallery_model.MonthTextRole)
            images = self.gallery_model.data(idx, self.gallery_model.ImagesRole)
            
            mw = MonthWidget(month_text, images, self.gallery_model, self.thumbnail_generator, self)
            self.content_layout.addWidget(mw)
            
            self.all_thumb_widgets.extend(mw.image_widgets)
            
        self.content_layout.addStretch()
        
        # Update selection state
        self.update_selection(self.gallery_model.get_selected_paths())
        
        # Check visibility
        QTimer.singleShot(10, self.check_visibility)

    @pyqtSlot()
    def check_visibility(self):
        viewport_rect = self.scroll_area.viewport().rect()
        
        # Optimization: Check visibility of MonthWidgets first
        # We need a list of MonthWidgets. We can reconstruct it or store it.
        # We can iterate layout items.
        
        for i in range(self.content_layout.count()):
            item = self.content_layout.itemAt(i)
            mw = item.widget()
            if not mw or not isinstance(mw, MonthWidget):
                continue
                
            # Check if MonthWidget is visible
            # Map mw position to viewport
            mw_geo = mw.geometry()
            # geometry() is in content_widget coordinates.
            # We need to map to viewport? 
            # content_widget is the widget OF scroll_area.
            # So visible region of content_widget IS viewport_rect (shifted by scroll).
            
            # Better: map content_widget's visible rect to mw coords?
            # Or map mw rect to viewport.
            
            # Simple check: 
            # mw top < viewport bottom AND mw bottom > viewport top
            
            # Convert viewport rect to content coordinates
            # visible_region = self.scroll_area.visibleRegion() # logic might be complex
            
            # Use mapToParent or mapTo(scroll_area.viewport())
            # Since content_layout is on content_widget, and content_widget is child of viewport (via setWidget)
            # Actually QScrollArea.widget() is a child of the viewport (or internal wrapper).
            
            # Let's just map the center or corners.
            # Fast check using mapped rect
            
            p_top_left = mw.mapTo(self.scroll_area.viewport(), QPoint(0,0))
            p_bottom_right = mw.mapTo(self.scroll_area.viewport(), QPoint(mw.width(), mw.height()))
            
            mw_rect_in_viewport = QRect(p_top_left, p_bottom_right)
            
            if viewport_rect.intersects(mw_rect_in_viewport):
                # This month is visible, check thumbnails
                for tw in mw.image_widgets:
                    if tw.is_loaded:
                        continue
                    
                    # Similar check for TW
                    tw_p = tw.mapTo(self.scroll_area.viewport(), QPoint(0,0))
                    tw_rect = QRect(tw_p, tw.size())
                    
                    if viewport_rect.intersects(tw_rect):
                        tw.load_thumbnail()

    @pyqtSlot(str, str)
    def on_thumbnail_ready(self, file_path, thumb_path):
        for tw in self.all_thumb_widgets:
            if tw.file_path == file_path:
                tw.set_thumbnail(thumb_path)

    @pyqtSlot(list)
    def update_selection(self, selected_paths):
        # Determine set for O(1) lookup
        sel_set = set(selected_paths)
        for tw in self.all_thumb_widgets:
            tw.set_selected(tw.file_path in sel_set)
