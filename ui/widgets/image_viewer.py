from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, 
    QPushButton, QFrame, QScrollArea, QListWidget, 
    QDialog, QSizePolicy, QGraphicsOpacityEffect, QStackedLayout
)
from PyQt6.QtCore import Qt, pyqtSlot, QSize, QTimer, QEvent, QRectF, pyqtSignal, QPointF, QPoint
from PyQt6.QtGui import QPixmap, QImage, QPainter, QIcon, QAction, QColor, QBrush, QPen, QCursor
from ui.widgets.tag_edit_dialog import TagEditDialog
from core.heic_provider import load_heic_to_qimage
from core.gallery_model import GalleryModel
import os

class ZoomableGraphicsView(QGraphicsView):
    interactionOccurred = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("background: transparent;")
        
        self.min_local_scale = 0.1 
        self.max_local_scale = 4.0
        self.fit_scale = 1.0
        self.scale_to_fit = True
        
        self._pixmap_item = None

    def set_image(self, pixmap):
        self.scene().clear()
        self.resetTransform()
        
        if pixmap and not pixmap.isNull():
            self._pixmap_item = QGraphicsPixmapItem(pixmap)
            self.scene().addItem(self._pixmap_item)
            self.setSceneRect(QRectF(pixmap.rect()))
            
            # Calculate fit scale
            self.calculate_fit_scale()
            self.reset_zoom()
        else:
            self._pixmap_item = None

    def calculate_fit_scale(self):
        if not self._pixmap_item:
            return
            
        view_rect = self.viewport().rect()
        scene_rect = self.sceneRect()
        
        if scene_rect.width() > 0 and scene_rect.height() > 0:
            x_scale = view_rect.width() / scene_rect.width()
            y_scale = view_rect.height() / scene_rect.height()
            self.fit_scale = min(x_scale, y_scale)
            # Ensure min scale allows for at least fitting (or smaller if image is huge)
            self.min_local_scale = min(self.fit_scale, 1.0) 

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.calculate_fit_scale()
        if self.scale_to_fit:
            self.reset_zoom()
        else:
            self.fix_bounds()

    def wheelEvent(self, event):
        self.interactionOccurred.emit()
        self.scale_to_fit = False
        
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        
        old_pos = self.mapToScene(event.position().toPoint())
        
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
            
        current_scale = self.transform().m11()
        new_scale = current_scale * zoom_factor
        
        # Clamp scale
        if new_scale > self.max_local_scale:
            new_scale = self.max_local_scale
            zoom_factor = new_scale / current_scale
        elif new_scale < self.min_local_scale:
            new_scale = self.min_local_scale
            zoom_factor = new_scale / current_scale

        self.scale(zoom_factor, zoom_factor)
        
        new_pos = self.mapToScene(event.position().toPoint())
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())
        
        self.fix_bounds()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.interactionOccurred.emit()

    def reset_zoom(self):
        self.scale_to_fit = True
        self.resetTransform()
        if self._pixmap_item:
             self.scale(self.fit_scale, self.fit_scale)
             self.centerOn(self.sceneRect().center())

    def set_zoom_1to1(self):
        self.scale_to_fit = False
        self.resetTransform()
        self.scale(1.0, 1.0)
        self.centerOn(self.sceneRect().center())
        self.fix_bounds()

    def fix_bounds(self):
        # Placeholder for boundary fixing if needed
        pass

class ImageDetailPanel(QWidget):
    closeRequested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gallery_model = GalleryModel.instance()
        self.current_path = ""
        self.setup_ui()
        
    def setup_ui(self):
        self.setFixedWidth(350)
        self.setStyleSheet("background-color: #2b2b2b; color: #e0e0e0; border-left: 1px solid #3d3d3d;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Details")
        title.setStyleSheet("font-size: 18px; font-weight: bold; border: none;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("background: transparent; border: none; font-size: 20px; color: #aaaaaa;")
        close_btn.clicked.connect(self.closeRequested.emit)
        header_layout.addWidget(close_btn)
        layout.addLayout(header_layout)
        
        # Content Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        content = QWidget()
        content.setStyleSheet("background: transparent; border: none;")
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(10)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
    def add_metadata_row(self, icon_name, text, is_link=False):
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(10)
        
        # Icon
        icon_label = QLabel()
        icon_path = f"assets/icons/{icon_name}"
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            if not pixmap.isNull():
                img = pixmap.toImage()
                img.invertPixels() # Simple inversion for white icons
                icon_label.setPixmap(QPixmap.fromImage(img))
        icon_label.setFixedSize(24, 24)
        icon_label.setStyleSheet("border: none;")
        row_layout.addWidget(icon_label)
        
        # Text
        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("border: none;")
        if is_link:
             text_label.setStyleSheet("color: #4facfe; text-decoration: underline; border: none;")
             text_label.setCursor(Qt.CursorShape.PointingHandCursor)
        row_layout.addWidget(text_label, 1)
        
        self.content_layout.addWidget(row)
        return row

    def load_details(self, path):
        self.current_path = path
        # Clear existing
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        details = self.gallery_model.get_image_details(path)
        if not details:
            return

        # Add Rows
        # Path (Folder)
        folder_path = os.path.dirname(path)
        folder_name = os.path.basename(folder_path)
        self.add_metadata_row("folder.svg", folder_name, is_link=True)
        
        self.add_metadata_row("calendar-clock.svg", details.get('date', 'Unknown'))
        self.add_metadata_row("hard-drive.svg", details.get('fileSize', 'Unknown'))
        self.add_metadata_row("size_icon.svg", details.get('imageSize', 'Unknown'))
        self.add_metadata_row("camera.svg", details.get('camera', 'Unknown'))
        self.add_metadata_row("noun-lens-8154880.svg", details.get('lens', 'Unknown'))
        self.add_metadata_row("aperture.svg", details.get('exifString', ''))
        
        # Tags Section
        tags_header = QLabel("Tags")
        tags_header.setStyleSheet("font-weight: bold; margin-top: 20px; border: none;")
        self.content_layout.addWidget(tags_header)
        
        tags = details.get('tags', [])
        if tags:
             tags_label = QLabel(", ".join(tags))
             tags_label.setWordWrap(True)
             tags_label.setStyleSheet("border: none;")
             self.content_layout.addWidget(tags_label)
        else:
             lbl = QLabel("No tags")
             lbl.setStyleSheet("color: #777; border: none;")
             self.content_layout.addWidget(lbl)
             
        # Add Tag Button
        add_tag_btn = QPushButton("Add Tag")
        add_tag_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_tag_btn.setStyleSheet("""
            QPushButton {
                background-color: #444;
                color: white;
                border-radius: 4px;
                padding: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        add_tag_btn.clicked.connect(self.open_tag_dialog)
        self.content_layout.addWidget(add_tag_btn)
        
        self.content_layout.addStretch()

    def open_tag_dialog(self):
        if not self.current_path:
            return
        dialog = TagEditDialog(target_path=self.current_path, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_details(self.current_path)

class ImageViewer(QWidget):
    closeRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.gallery_model = GalleryModel.instance()
        self.current_path = ""
        self.controls_visible = True
        
        self.setStyleSheet("background-color: black;")
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.view = ZoomableGraphicsView()
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        self.view.interactionOccurred.connect(self.on_interaction)
        
        self.layout.addWidget(self.view)
        
        # Side Panel
        self.detail_panel = ImageDetailPanel()
        self.detail_panel.closeRequested.connect(self.closeRequested.emit)
        self.layout.addWidget(self.detail_panel)
        
        # Overlays
        self.setup_overlays()
        
        # Auto-hide timer
        self.hide_timer = QTimer(self)
        self.hide_timer.setInterval(2000)
        self.hide_timer.timeout.connect(self.hide_controls)
        self.hide_timer.start()
        
        self.setMouseTracking(True)
        self.view.setMouseTracking(True)
        
        # Actions
        self.next_act = QAction(self)
        self.next_act.setShortcut("Right")
        self.next_act.triggered.connect(self.next_image)
        self.addAction(self.next_act)
        
        self.prev_act = QAction(self)
        self.prev_act.setShortcut("Left")
        self.prev_act.triggered.connect(self.prev_image)
        self.addAction(self.prev_act)
        
        self.esc_act = QAction(self)
        self.esc_act.setShortcut("Esc")
        self.esc_act.triggered.connect(self.on_escape)
        self.addAction(self.esc_act)

    def setup_overlays(self):
        # Back Button (Top Left)
        self.back_btn = QPushButton(self)
        self.back_btn.setIcon(QIcon("assets/icons/arrow-left.svg"))
        self.back_btn.setFixedSize(40, 40)
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.clicked.connect(self.closeRequested.emit)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0,0,0,100); 
                border-radius: 20px; 
                border: 1px solid rgba(255,255,255,50);
            }
            QPushButton:hover {
                background: rgba(50,50,50,150);
            }
        """)
        
        # Zoom Controls (Top Center)
        self.zoom_controls = QFrame(self)
        self.zoom_controls.setStyleSheet("background: rgba(0,0,0,100); border-radius: 10px; border: 1px solid rgba(255,255,255,50);")
        self.zoom_controls.setFixedHeight(40)
        self.zoom_controls.setFixedWidth(120)
        
        z_layout = QHBoxLayout(self.zoom_controls)
        z_layout.setContentsMargins(5, 5, 5, 5)
        
        fit_btn = QPushButton("Fit")
        fit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        fit_btn.setStyleSheet("background: transparent; color: white; border: none; font-weight: bold;")
        fit_btn.clicked.connect(lambda: self.view.reset_zoom())
        z_layout.addWidget(fit_btn)
        
        one_btn = QPushButton("1:1")
        one_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        one_btn.setStyleSheet("background: transparent; color: white; border: none; font-weight: bold;")
        one_btn.clicked.connect(lambda: self.view.set_zoom_1to1())
        z_layout.addWidget(one_btn)
        
        # Nav Buttons
        self.prev_btn = QPushButton(self)
        self.prev_btn.setIcon(QIcon("assets/icons/arrow-left.svg"))
        self.prev_btn.setFixedSize(50, 50)
        self.prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_btn.clicked.connect(self.prev_image)
        self.prev_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0,0,0,100); 
                border-radius: 25px; 
                border: 1px solid rgba(255,255,255,50);
            }
            QPushButton:hover {
                background: rgba(50,50,50,150);
            }
        """)
        
        self.next_btn = QPushButton(self)
        self.next_btn.setIcon(QIcon("assets/icons/arrow-right.svg"))
        self.next_btn.setFixedSize(50, 50)
        self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_btn.clicked.connect(self.next_image)
        self.next_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0,0,0,100); 
                border-radius: 25px; 
                border: 1px solid rgba(255,255,255,50);
            }
            QPushButton:hover {
                background: rgba(50,50,50,150);
            }
        """)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Position overlays
        self.back_btn.move(20, 20)
        
        # Center zoom controls relative to the view area (excluding detail panel)
        view_width = self.view.width()
        self.zoom_controls.move((view_width - self.zoom_controls.width()) // 2, 20)
        
        # Vertical centering for nav buttons
        center_y = (self.height() - 50) // 2
        self.prev_btn.move(20, center_y)
        self.next_btn.move(view_width - 70, center_y)

    def mouseMoveEvent(self, event):
        self.show_controls()
        super().mouseMoveEvent(event)

    def on_interaction(self):
        self.show_controls()

    def show_controls(self):
        if not self.controls_visible:
            self.controls_visible = True
            self.back_btn.show()
            self.zoom_controls.show()
            self.prev_btn.show()
            self.next_btn.show()
            self.setCursor(Qt.CursorShape.ArrowCursor)
            
        self.hide_timer.start()

    def hide_controls(self):
        # Don't hide if mouse is over a button
        for child in self.children():
            if isinstance(child, QPushButton) or isinstance(child, QFrame):
                if child.isVisible() and child.geometry().contains(self.mapFromGlobal(QCursor.pos())):
                     return
                     
        self.controls_visible = False
        self.back_btn.hide()
        self.zoom_controls.hide()
        self.prev_btn.hide()
        self.next_btn.hide()
        # self.setCursor(Qt.CursorShape.BlankCursor) # Optional: hide cursor too

    def on_escape(self):
        self.closeRequested.emit()

    def open(self, path):
        self.current_path = path
        self.detail_panel.load_details(path)
        self.load_image()
        self.show_controls()
        
    def load_image(self):
        if not os.path.exists(self.current_path):
             return
             
        pixmap = None
        lower_path = self.current_path.lower()
        if lower_path.endswith('.heic') or lower_path.endswith('.heif'):
             qimg = load_heic_to_qimage(self.current_path)
             if not qimg.isNull():
                 pixmap = QPixmap.fromImage(qimg)
        else:
             pixmap = QPixmap(self.current_path)
             
        self.view.set_image(pixmap)

    def next_image(self):
        next_path = self.gallery_model.get_next_image_path(self.current_path)
        if next_path:
            self.open(next_path)

    def prev_image(self):
        prev_path = self.gallery_model.get_previous_image_path(self.current_path)
        if prev_path:
            self.open(prev_path)
