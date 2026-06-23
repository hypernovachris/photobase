from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QStyleOptionGraphicsItem,
    QPushButton, QFrame, QScrollArea, QListWidget, 
    QDialog, QSizePolicy, QGraphicsOpacityEffect, QStackedLayout,
    QMessageBox, QProgressDialog
)
from PyQt6.QtCore import Qt, pyqtSlot, QSize, QTimer, QEvent, QRectF, pyqtSignal, QPointF, QPoint, QThread
from PyQt6.QtGui import QPixmap, QImage, QPainter, QIcon, QAction, QColor, QBrush, QPen, QCursor, QImageReader
from ui.widgets.tag_edit_dialog import TagEditDialog
from core.heic_provider import load_heic_to_qimage
from core.gallery_model import GalleryModel
from ui.widgets.util.flow_layout import FlowLayout
import os
import math

class MipmappedGraphicsPixmapItem(QGraphicsPixmapItem):
    def __init__(self, pixmap, mipmaps=None, parent=None):
        super().__init__(pixmap, parent)
        self._original_pixmap = pixmap
        
        if mipmaps:
            self._mipmaps = mipmaps
        else:
            self._mipmaps = {1.0: pixmap}
            if pixmap and not pixmap.isNull():
                current_pixmap = pixmap
                current_scale = 1.0
                # Progressively generate downscaled mipmaps down to ~5% scale or min 100px width/height
                while current_pixmap.width() > 100 and current_pixmap.height() > 100 and current_scale > 0.05:
                    next_scale = current_scale * 0.5
                    next_width = int(current_pixmap.width() * 0.5)
                    next_height = int(current_pixmap.height() * 0.5)
                    if next_width <= 0 or next_height <= 0:
                        break
                    next_pixmap = current_pixmap.scaled(
                        next_width,
                        next_height,
                        Qt.AspectRatioMode.IgnoreAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self._mipmaps[next_scale] = next_pixmap
                    current_pixmap = next_pixmap
                    current_scale = next_scale

        self.setTransformationMode(Qt.TransformationMode.SmoothTransformation)

    def paint(self, painter, option, widget=None):
        if not self._original_pixmap or self._original_pixmap.isNull():
            super().paint(painter, option, widget)
            return

        # Calculate level of detail (current zoom/scale factor)
        lod = QStyleOptionGraphicsItem.levelOfDetailFromTransform(painter.worldTransform())

        # Select the best mipmap level (smallest scale >= lod)
        available_scales = sorted(self._mipmaps.keys(), reverse=True)
        chosen_scale = 1.0
        for scale in available_scales:
            if scale >= lod:
                chosen_scale = scale
            else:
                break

        pixmap = self._mipmaps[chosen_scale]

        # Draw the selected mipmap to fill the original bounding rect
        painter.setRenderHint(
            QPainter.RenderHint.SmoothPixmapTransform,
            self.transformationMode() == Qt.TransformationMode.SmoothTransformation
        )
        painter.drawPixmap(self.boundingRect(), pixmap, QRectF(pixmap.rect()))

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
        self.setStyleSheet("background: #000000;")
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        self.min_local_scale = 0.1 
        self.max_local_scale = 4.0
        self.fit_scale = 1.0
        self.scale_to_fit = True
        
        self._pixmap_item = None

    def set_image(self, pixmap, mipmaps=None):
        self.scene().clear()
        self.resetTransform()
        
        if pixmap and not pixmap.isNull():
            self._pixmap_item = MipmappedGraphicsPixmapItem(pixmap, mipmaps)
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

class TagChip(QFrame):
    removeRequested = pyqtSignal(str)

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text = text
        self.setup_ui()

    def setup_ui(self):
        self.setObjectName("TagChip")
        self.setStyleSheet("""
            #TagChip {
                background-color: #444;
                border-radius: 12px;
                border: 1px solid #555;
            }
            #TagChip:hover {
                background-color: #555;
                border: 1px solid #666;
            }
        """)
        self.setFixedHeight(24)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 4, 0) # Left padding for text, right for button
        layout.setSpacing(4)
        
        # Tag Name
        label = QLabel(self.text)
        label.setStyleSheet("color: #eee; font-size: 11px; border: none; background: transparent;")
        layout.addWidget(label)
        
        # Remove Button
        btn = QPushButton("×")
        btn.setFixedSize(16, 16)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self.removeRequested.emit(self.text))
        btn.setStyleSheet("""
            QPushButton {
                color: #aaa;
                border: none;
                background: transparent;
                font-size: 14px;
                font-weight: bold;
                padding-bottom: 2px;
            }
            QPushButton:hover {
                color: #fff;
                background: rgba(255, 255, 255, 30);
                border-radius: 8px;
            }
        """)
        layout.addWidget(btn)

class ImageDetailPanel(QWidget):
    closeRequested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gallery_model = GalleryModel.instance()
        self.current_path = ""
        self.setup_ui()
        
    def setup_ui(self):
        self.setFixedWidth(350)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #2b2b2b; color: #e0e0e0; border-left: 1px solid #3d3d3d;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        self.header_label = QLabel("Details")
        self.header_label.setStyleSheet("font-size: 16px; font-weight: bold; border: none;")
        self.header_label.setWordWrap(True)
        self.header_label.setOpenExternalLinks(False)
        self.header_label.linkActivated.connect(self.on_header_clicked)
        header_layout.addWidget(self.header_label, 1)
        
        header_layout.addStretch()
        
        close_btn = QPushButton()
        close_btn.setIcon(QIcon("assets/icons/x.svg"))
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
        
    def add_metadata_row(self, icon_name, text, is_link=False, on_click=None):
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(10)
        
        # Icon
        icon_label = QLabel()
        icon_path = f"assets/icons/{icon_name}"
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            if not pixmap.isNull():
                img = pixmap.toImage()
                icon_label.setPixmap(QPixmap.fromImage(img))
        icon_label.setFixedSize(24, 24)
        icon_label.setStyleSheet("border: none;")
        row_layout.addWidget(icon_label)
        
        # Text
        text_label = QLabel()
        text_label.setWordWrap(True)
        text_label.setStyleSheet("border: none;")
        
        if is_link:
             # Use HTML for link
             # Ensure text is escaped if needed, but for filenames it's mostly fine or we should escape.
             # Minimal escape:
             safe_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             text_label.setText(f'<a href="#" style="color: #4facfe; text-decoration: underline;">{safe_text}</a>')
             text_label.setCursor(Qt.CursorShape.PointingHandCursor)
             text_label.setTextFormat(Qt.TextFormat.RichText)
             text_label.setOpenExternalLinks(False)
             if on_click:
                 text_label.linkActivated.connect(lambda link: on_click())
        else:
             text_label.setText(text)
             
        row_layout.addWidget(text_label, 1)
        
        self.content_layout.addWidget(row)
        return row

    def load_basic_details(self, path):
        self.current_path = path
        # Clear existing
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        filename = os.path.basename(path)
        safe_filename = filename.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self.header_label.setText(f'<a href="#" style="color: #e0e0e0; text-decoration: none;">{safe_filename}</a>')
        self.header_label.setToolTip("Click to open file")
        self.header_label.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Add basic loading skeleton rows
        self.add_metadata_row("folder.svg", "Loading folder...")
        self.add_metadata_row("calendar-clock.svg", "Loading date...")
        self.add_metadata_row("hard-drive.svg", "Loading size...")
        self.add_metadata_row("size_icon.svg", "Loading dimensions...")

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
        # Filename in Header
        filename = os.path.basename(path)
        # Escape filename for HTML
        safe_filename = filename.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self.header_label.setText(f'<a href="#" style="color: #e0e0e0; text-decoration: none;">{safe_filename}</a>')
        self.header_label.setToolTip("Click to open file")
        self.header_label.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Path (Folder)
        folder_path = os.path.dirname(path)
        folder_name = os.path.basename(folder_path)
        self.add_metadata_row("folder.svg", folder_name, is_link=True, on_click=lambda: self.gallery_model.reveal_file(path))
        
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
        
        # Flow Layout Container
        tags_container = QWidget()
        tags_container.setStyleSheet("background: transparent; border: none;")
        self.tags_flow = FlowLayout(tags_container)
        self.tags_flow.setContentsMargins(0, 0, 0, 0)
        self.tags_flow.setSpacing(6)
        self.content_layout.addWidget(tags_container)

        tags = details.get('tags', [])
        if tags:
             for tag in tags:
                 chip = TagChip(tag)
                 chip.removeRequested.connect(self.remove_tag)
                 self.tags_flow.addWidget(chip)
        else:
             lbl = QLabel("No tags")
             lbl.setStyleSheet("color: #777; border: none;")
             # Add to flow to position it correctly and ensure it gets deleted when tags_container is cleared
             self.tags_flow.addWidget(lbl)
             
        # Add Tag Button
        add_tag_container = QWidget()
        add_tag_layout = QHBoxLayout(add_tag_container)
        add_tag_layout.setContentsMargins(0, 10, 0, 0) # Margin top
        add_tag_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        add_tag_btn = QPushButton("Add Tag")
        add_tag_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_tag_btn.setIcon(QIcon("assets/icons/plus.svg"))
        add_tag_btn.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: #ccc;
                border-radius: 4px;
                padding: 6px 12px;
                border: 1px solid #444;
            }
            QPushButton:hover {
                background-color: #444;
                color: white;
                border: 1px solid #555;
            }
        """)
        add_tag_btn.clicked.connect(self.open_tag_dialog)
        add_tag_layout.addWidget(add_tag_btn)
        
        self.content_layout.addWidget(add_tag_container)
        
        self.content_layout.addStretch()

    def remove_tag(self, tag_name):
        if self.current_path:
            self.gallery_model.remove_tag_from_image_path(self.current_path, tag_name)
            self.load_details(self.current_path)

    def open_tag_dialog(self):
        if not self.current_path:
            return
        dialog = TagEditDialog(target_path=self.current_path, parent=self, add_tags=True)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_details(self.current_path)

    def on_header_clicked(self, link):
        if self.current_path:
            self.gallery_model.open_file(self.current_path)

class ImageLoaderThread(QThread):
    image_loaded = pyqtSignal(str, QImage, object) # path, image, mipmaps
    
    def __init__(self, path):
        super().__init__()
        self.path = path
        self._is_cancelled = False
        
    def cancel(self):
        self._is_cancelled = True
        
    def run(self):
        if self._is_cancelled:
            return
            
        try:
            lower_path = self.path.lower()
            qimg = None
            if lower_path.endswith('.heic') or lower_path.endswith('.heif'):
                qimg = load_heic_to_qimage(self.path)
            else:
                reader = QImageReader(self.path)
                reader.setAutoTransform(True)
                qimg = reader.read()
                
            if qimg is None or qimg.isNull():
                return
                
            if self._is_cancelled:
                return
                
            # Compute mipmap QImages in the background
            mipmaps = {1.0: qimg}
            current_qimg = qimg
            current_scale = 1.0
            
            while current_qimg.width() > 100 and current_qimg.height() > 100 and current_scale > 0.05:
                if self._is_cancelled:
                    return
                next_scale = current_scale * 0.5
                next_width = int(current_qimg.width() * 0.5)
                next_height = int(current_qimg.height() * 0.5)
                if next_width <= 0 or next_height <= 0:
                    break
                next_qimg = current_qimg.scaled(
                    next_width,
                    next_height,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                mipmaps[next_scale] = next_qimg
                current_qimg = next_qimg
                current_scale = next_scale
                
            if self._is_cancelled:
                return
                
            self.image_loaded.emit(self.path, qimg, mipmaps)
            
        except Exception as e:
            print(f"Error loading image in background thread: {e}")

class ImageViewer(QWidget):
    closeRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.gallery_model = GalleryModel.instance()
        self.current_path = ""
        self.controls_visible = True
        
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("ImageViewer { background-color: black; }")
        
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
        
        self.loader_thread = None
        self.active_threads = set()
        
        # Debounce timer for async image and metadata loading
        self.debounce_timer = QTimer(self)
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.setInterval(150) # 150ms debounce
        self.debounce_timer.timeout.connect(self.on_debounce_timeout)
        
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

        self.del_act = QAction(self)
        self.del_act.setShortcut("Delete")
        self.del_act.triggered.connect(self.delete_current_image)
        self.addAction(self.del_act)

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
                border-radius: 10px; 
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
        
        fit_btn = QPushButton()
        fit_btn.setIcon(QIcon("assets/icons/zoom_fit.svg"))
        fit_btn.setFixedSize(24, 24)
        fit_btn.setIconSize(QSize(24, 24))
        fit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        fit_btn.setStyleSheet("background: transparent; color: white; border: none; font-weight: bold;")
        fit_btn.clicked.connect(lambda: self.view.reset_zoom())
        z_layout.addWidget(fit_btn)
        
        one_btn = QPushButton()
        one_btn.setIcon(QIcon("assets/icons/zoom_1to1.svg"))
        one_btn.setFixedSize(24, 24)
        one_btn.setIconSize(QSize(24, 24))
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
                border-radius: 10px; 
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
                border-radius: 10px; 
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
        
        # Cancel any active loader thread immediately to free up resources
        try:
            if self.loader_thread and self.loader_thread.isRunning():
                self.loader_thread.cancel()
                try:
                    self.loader_thread.image_loaded.disconnect(self.on_image_loaded)
                except TypeError:
                    pass
        except RuntimeError:
            self.loader_thread = None
            
        # Stop debounce timer
        self.debounce_timer.stop()
        
        # Show basic details immediately (filename and skeleton rows)
        self.detail_panel.load_basic_details(path)
        
        # Load thumbnail placeholder immediately
        self.load_thumbnail_placeholder()
        
        # Start debounce timer for loading full resolution and metadata
        self.debounce_timer.start()
        
        self.show_controls()

    def get_image_dimensions(self, path):
        try:
            lower_path = path.lower()
            if lower_path.endswith('.heic') or lower_path.endswith('.heif'):
                from PIL import Image
                with Image.open(path) as img:
                    return img.size
            else:
                reader = QImageReader(path)
                if reader.supportsOption(QImageReader.ImageOption.Size):
                    sz = reader.size()
                    if sz.isValid():
                        return sz.width(), sz.height()
                from PIL import Image
                with Image.open(path) as img:
                    return img.size
        except Exception:
            return None

    def create_placeholder_pixmap(self, thumb_path, original_width, original_height):
        thumb = QPixmap(thumb_path)
        if thumb.isNull():
            return QPixmap()
            
        # Limit the placeholder QPixmap size to keep it lightweight (max 800px)
        max_size = 800
        aspect = original_width / original_height
        if original_width > original_height:
            w = max_size
            h = int(max_size / aspect)
        else:
            h = max_size
            w = int(max_size * aspect)
            
        if w <= 0 or h <= 0:
            return thumb
            
        placeholder = QPixmap(w, h)
        placeholder.fill(QColor(0, 0, 0)) # Fill black
        
        painter = QPainter(placeholder)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Center the square thumbnail in the placeholder
        if w > h:
            # Landscape
            target_rect = QRectF((w - h) / 2.0, 0.0, float(h), float(h))
        else:
            # Portrait/Square
            target_rect = QRectF(0.0, (h - w) / 2.0, float(w), float(w))
            
        painter.drawPixmap(target_rect, thumb, QRectF(thumb.rect()))
        painter.end()
        return placeholder

    def load_thumbnail_placeholder(self):
        if not self.current_path or not os.path.exists(self.current_path):
            self.view.set_image(QPixmap())
            return
            
        import hashlib
        thumb_hash = hashlib.md5(self.current_path.encode()).hexdigest()
        thumb_path = os.path.join("thumbnails", f"{thumb_hash}.jpg")
        
        if os.path.exists(thumb_path):
            size = self.get_image_dimensions(self.current_path)
            if size:
                w, h = size
                placeholder = self.create_placeholder_pixmap(thumb_path, w, h)
                self.view.set_image(placeholder)
            else:
                self.view.set_image(QPixmap(thumb_path))
        else:
            self.view.set_image(QPixmap()) # Black screen

    def on_debounce_timeout(self):
        # 1. Load full details (exif, etc.)
        self.detail_panel.load_details(self.current_path)
        
        # 2. Start asynchronous loading of full image
        self.start_async_load_image()

    def start_async_load_image(self):
        if not self.current_path or not os.path.exists(self.current_path):
            return
            
        # Cancel and disconnect any existing thread
        try:
            if self.loader_thread and self.loader_thread.isRunning():
                self.loader_thread.cancel()
                try:
                    self.loader_thread.image_loaded.disconnect(self.on_image_loaded)
                except TypeError:
                    pass
        except RuntimeError:
            self.loader_thread = None
                
        thread = ImageLoaderThread(self.current_path)
        thread.image_loaded.connect(self.on_image_loaded)
        # Protect against python GC
        self.active_threads.add(thread)
        
        def cleanup(t=thread):
            self.active_threads.discard(t)
            try:
                if self.loader_thread == t:
                    self.loader_thread = None
            except RuntimeError:
                pass
                
        thread.finished.connect(cleanup)
        thread.finished.connect(thread.deleteLater)
        self.loader_thread = thread
        thread.start()

    def on_image_loaded(self, path, qimage, mipmap_qimages):
        # Prevent race condition (discard if user already navigated away)
        if path != self.current_path:
            return
            
        pixmap = QPixmap.fromImage(qimage)
        
        # Convert mipmap QImages to QPixmaps
        mipmaps = {}
        for scale, qimg in mipmap_qimages.items():
            if qimg and not qimg.isNull():
                mipmaps[scale] = QPixmap.fromImage(qimg)
            
        self.view.set_image(pixmap, mipmaps)

    def next_image(self):
        next_path = self.gallery_model.get_next_image_path(self.current_path)
        if next_path:
            self.open(next_path)

    def prev_image(self):
        prev_path = self.gallery_model.get_previous_image_path(self.current_path)
        if prev_path:
            self.open(prev_path)

    def delete_current_image(self):
        if not self.current_path or not os.path.exists(self.current_path):
            return

        # Determine the next image path to navigate to *before* deletion starts.
        next_path = self.gallery_model.get_next_image_path(self.current_path)
        if not next_path:
            # If no next image, try the previous image
            next_path = self.gallery_model.get_previous_image_path(self.current_path)

        self.next_path_after_delete = next_path

        from ui.widgets.util.recycle_worker import can_recycle_path, RecycleWorker

        selected = [self.current_path]

        # 1. Pre-check if the file can be recycled
        permanent_mode = False
        if any(not can_recycle_path(path) for path in selected):
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Warning")
            msg_box.setText("The selected item cannot be recycled. Proceeding with this action will permanently delete it. Proceed anyway?")
            proceed_button = msg_box.addButton("Proceed Anyway", QMessageBox.ButtonRole.AcceptRole)
            cancel_button = msg_box.addButton(QMessageBox.StandardButton.Cancel)
            msg_box.setDefaultButton(cancel_button)
            msg_box.exec()

            if msg_box.clickedButton() == cancel_button:
                return
            permanent_mode = True

        # 2. Confirmation dialogue
        confirm_box = QMessageBox(self)
        confirm_box.setWindowTitle("Confirm Action")
        if permanent_mode:
            confirm_box.setText("Permanently delete this item?")
        else:
            confirm_box.setText("Recycle this item?")

        yes_button = confirm_box.addButton(QMessageBox.StandardButton.Yes)
        cancel_button = confirm_box.addButton(QMessageBox.StandardButton.Cancel)
        confirm_box.setDefaultButton(cancel_button)
        confirm_box.exec()

        if confirm_box.clickedButton() == cancel_button:
            return

        # 3. Show non-cancelable window-modal progress bar dialog
        self.progress_dialog = QProgressDialog("Deleting files...", None, 0, len(selected), self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.show()

        # 4. Start worker
        self.worker = RecycleWorker(selected, permanent_mode)
        self.worker.progress.connect(self.progress_dialog.setValue)
        self.worker.fileRemoved.connect(self.gallery_model.handle_file_removed)
        self.worker.finished.connect(lambda succeeded: self.on_recycle_finished(succeeded, permanent_mode))
        self.worker.error.connect(lambda err_msg, succeeded, total: self.on_recycle_error(err_msg, succeeded, total, permanent_mode))
        self.worker.start()

    def on_recycle_finished(self, succeeded, permanent_mode):
        self.progress_dialog.close()

        self.gallery_model.clear_selection()
        self.gallery_model.refresh()

        if succeeded > 0:
            if self.next_path_after_delete:
                self.open(self.next_path_after_delete)
            else:
                self.closeRequested.emit()

    def on_recycle_error(self, err_msg, succeeded, total, permanent_mode):
        self.progress_dialog.close()

        action_text = "permanently deleted" if permanent_mode else "recycled"
        QMessageBox.warning(
            self,
            "Error",
            f"An error occurred. {succeeded}/{total} items were {action_text}"
        )

        self.gallery_model.clear_selection()
        self.gallery_model.refresh()

        # If we succeeded partially and the deleted file was the current image, we should probably update
        if succeeded > 0 and not os.path.exists(self.current_path):
            if self.next_path_after_delete:
                self.open(self.next_path_after_delete)
            else:
                self.closeRequested.emit()
