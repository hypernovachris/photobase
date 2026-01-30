from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, 
    QPushButton, QFrame, QScrollArea, QListWidget, QListWidgetItem,
    QDialog, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSlot, QSize, QTimer, QEvent, QRectF, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QPainter, QIcon, QTransform, QAction, QColor, QFont
from core.theme import Theme
from ui.widgets.tag_edit_dialog import TagEditDialog
from core.heic_provider import load_heic_to_qimage
import os

class ZoomableGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.bg_color = QColor(0, 0, 0, 200) # Semi-transparent black
        self.setStyleSheet("background: transparent;")

    def wheelEvent(self, event):
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        self.scale(zoom_factor, zoom_factor)

class ImageDetailPanel(QWidget):
    def __init__(self, gallery_model, parent=None):
        super().__init__(parent)
        self.gallery_model = gallery_model
        self.current_path = ""
        
        self.setup_ui()
        
    def setup_ui(self):
        self.setFixedWidth(350)
        self.setStyleSheet(f"background-color: {Theme.secondaryBackgroundColor.name()}; color: {Theme.textColor.name()};")
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header = QLabel("Image Details")
        header.setStyleSheet(f"font-size: {Theme.fontSizeHeader}px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Info
        self.info_label = QLabel("Loading...")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet(f"font-size: {Theme.fontSizeBody}px;")
        layout.addWidget(self.info_label)
        
        # Tags List
        layout.addWidget(QLabel("Tags:"))
        self.tags_list = QListWidget()
        self.tags_list.setStyleSheet(f"background-color: {Theme.backgroundColor.name()}; border: 1px solid {Theme.borderColor.name()};")
        layout.addWidget(self.tags_list)
        
        # Edit Tags Button
        self.edit_tags_btn = QPushButton("Edit Tags")
        self.edit_tags_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.buttonColor.name()}; 
                padding: 8px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {Theme.highlightColor.name()};
                color: white;
            }}
        """)
        self.edit_tags_btn.clicked.connect(self.open_tag_dialog)
        layout.addWidget(self.edit_tags_btn)
        
        layout.addStretch()

    def load_details(self, path):
        self.current_path = path
        details = self.gallery_model.get_image_details(path)
        
        if not details:
            self.info_label.setText("Could not load details.")
            self.tags_list.clear()
            return

        # Handle potential missing keys gracefully
        date_str = details.get('date', 'Unknown')
        camera = details.get('camera', 'Unknown')
        lens = details.get('lens', 'Unknown')
        img_size = details.get('imageSize', 'Unknown')
        file_size = details.get('fileSize', 'Unknown')
        exif = details.get('exifString', '')
            
        info_text = f"<b>Date:</b> {date_str}<br>"
        info_text += f"<b>Camera:</b> {camera}<br>"
        info_text += f"<b>Lens:</b> {lens}<br>"
        info_text += f"<b>Resolution:</b> {img_size}<br>"
        info_text += f"<b>File Size:</b> {file_size}<br>"
        if exif:
            info_text += f"<b>EXIF:</b> {exif}"
        
        self.info_label.setText(info_text)
        
        self.tags_list.clear()
        for tag in details.get('tags', []):
            self.tags_list.addItem(tag)

    def open_tag_dialog(self):
        if not self.current_path:
            return
        
        dialog = TagEditDialog(self.gallery_model, target_path=self.current_path, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_details(self.current_path) # Refresh

class ImageViewer(QWidget):
    closeRequested = pyqtSignal()

    def __init__(self, gallery_model, parent=None):
        super().__init__(parent)
        self.gallery_model = gallery_model
        self.current_path = ""
        
        # self.setWindowTitle("Image Viewer") # Not needed as embedded
        # self.resize(1200, 800)
        self.setStyleSheet(f"background-color: black;") 
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Toolbar / Header
        self.toolbar = QWidget()
        self.toolbar.setFixedHeight(50)
        self.toolbar.setStyleSheet(f"background-color: {Theme.backgroundColor.name()};")
        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(10, 0, 10, 0)
        
        # Back Button
        back_btn = QPushButton("Back to Library")
        back_btn.setStyleSheet(f"color: {Theme.textColor.name()}; border: none; font-weight: bold;")
        back_btn.setIcon(QIcon("assets/icons/arrow-left.svg")) # Placeholder if icon missing
        back_btn.clicked.connect(self.closeRequested.emit)
        toolbar_layout.addWidget(back_btn)
        
        toolbar_layout.addStretch()
        
        # Zoom Controls
        zoom_out_btn = QPushButton("-")
        zoom_out_btn.setFixedSize(30, 30)
        zoom_out_btn.clicked.connect(lambda: self.view.scale(0.8, 0.8))
        toolbar_layout.addWidget(zoom_out_btn)
        
        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setFixedSize(30, 30)
        zoom_in_btn.clicked.connect(lambda: self.view.scale(1.25, 1.25))
        toolbar_layout.addWidget(zoom_in_btn)
        
        fit_btn = QPushButton("Fit")
        fit_btn.setFixedSize(40, 30)
        fit_btn.clicked.connect(self.fit_image)
        toolbar_layout.addWidget(fit_btn)
        
        toolbar_layout.addStretch()
        
        # Nav Controls
        prev_btn = QPushButton("<")
        prev_btn.setFixedSize(30, 30)
        prev_btn.clicked.connect(self.prev_image)
        toolbar_layout.addWidget(prev_btn)
        
        next_btn = QPushButton(">")
        next_btn.setFixedSize(30, 30)
        next_btn.clicked.connect(self.next_image)
        toolbar_layout.addWidget(next_btn)

        main_layout.addWidget(self.toolbar)

        # Content Area
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Graphics View for Image
        self.scene = QGraphicsScene()
        self.view = ZoomableGraphicsView()
        self.view.setScene(self.scene)
        content_layout.addWidget(self.view, 1)
        
        # Side Panel
        self.detail_panel = ImageDetailPanel(self.gallery_model)
        content_layout.addWidget(self.detail_panel)
        
        main_layout.addWidget(content)
        
        # Navigation Actions (Shortcuts)
        self.next_act = QAction("Next Image", self)
        self.next_act.setShortcut("Right")
        self.next_act.triggered.connect(self.next_image)
        self.addAction(self.next_act)
        
        self.prev_act = QAction("Previous Image", self)
        self.prev_act.setShortcut("Left")
        self.prev_act.triggered.connect(self.prev_image)
        self.addAction(self.prev_act)
        
        self.esc_act = QAction("Close", self)
        self.esc_act.setShortcut("Esc")
        self.esc_act.triggered.connect(self.closeRequested.emit)
        self.addAction(self.esc_act)

    def open(self, path):
        self.current_path = path
        # self.show() # Controlled by StackedWidget
        
        self.load_image()
        self.detail_panel.load_details(path)
        
    def fit_image(self):
        if not self.scene.items():
            return
        self.view.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def load_image(self):
        self.scene.clear()
        self.view.resetTransform()
        
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
             
        if pixmap and not pixmap.isNull():
            item = QGraphicsPixmapItem(pixmap)
            self.scene.addItem(item)
            
            # Fit in view
            self.scene.setSceneRect(QRectF(pixmap.rect()))
            self.fit_image()
        else:
             print(f"Failed to load image: {self.current_path}")

    def next_image(self):
        next_path = self.gallery_model.get_next_image_path(self.current_path)
        if next_path:
            self.open(next_path)

    def prev_image(self):
        prev_path = self.gallery_model.get_previous_image_path(self.current_path)
        if prev_path:
            self.open(prev_path)
