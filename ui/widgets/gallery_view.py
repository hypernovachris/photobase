from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSlot
from core.gallery_model import GalleryModel
from core.thumbnail_generator import ThumbnailGenerator
from ui.widgets.gallery_list_view import GalleryListView
from ui.widgets.gallery_item_delegate import GalleryItemDelegate

class GalleryView(QWidget):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.gallery_model = GalleryModel.instance()
    self.thumbnail_generator = ThumbnailGenerator.instance()
    
    self.thumbnail_generator.thumbnailReady.connect(self.on_thumbnail_ready)
    self.gallery_model.selectionChanged.connect(self.update_selection)
    self.gallery_model.countChanged.connect(self.populate_view)
    self.gallery_model.filterChanged.connect(self.update_banner)

    self.main_layout = QVBoxLayout(self)
    
    # --- Filter Banner ---
    self.banner_container = QWidget()
    self.banner_layout = QHBoxLayout(self.banner_container)
    self.banner_layout.setContentsMargins(10, 5, 10, 5)
    self.banner_layout.setSpacing(10)
    
    self.banner_label = QLabel()
    self.banner_label.setStyleSheet("font-weight: bold; font-size: 14px;")
    
    self.clear_filter_btn = QPushButton("Clear Filter")
    self.clear_filter_btn.clicked.connect(self.gallery_model.clear_filter)
    
    self.banner_layout.addWidget(self.banner_label)
    self.banner_layout.addWidget(self.clear_filter_btn)
    self.banner_layout.addStretch()
    
    self.banner_container.setVisible(False)
    self.main_layout.addWidget(self.banner_container)

    # Virtualized ListView
    self.list_view = GalleryListView(self)
    self.delegate = GalleryItemDelegate(self.list_view)
    self.list_view.setItemDelegate(self.delegate)
    self.list_view.setModel(self.gallery_model)
    
    self.main_layout.addWidget(self.list_view)
    self.setLayout(self.main_layout)
    
    # Initial Population
    self.populate_view()

  @pyqtSlot()
  def populate_view(self):
    # Update Banner Visualization based on current model state
    self.update_banner(self.gallery_model.get_active_filter())

  @pyqtSlot(str)
  def update_banner(self, filter_name):
      if filter_name:
          self.banner_label.setText(f"Filtering by: {filter_name}")
          self.banner_container.setVisible(True)
      else:
          self.banner_container.setVisible(False)

  @pyqtSlot(str)
  def on_thumbnail_ready(self, file_path):
    # Find which row in the model contains this file_path and update it surgically
    for r in range(self.gallery_model.rowCount()):
        index = self.gallery_model.index(r, 0)
        item = index.data(Qt.ItemDataRole.UserRole)
        if item and item.get("type") == "images":
            for img in item.get("images", []):
                if img["path"] == file_path:
                    # Invalidate local thumbnail pixmap cache in delegate
                    if file_path in self.delegate.thumb_cache:
                        self.delegate.thumb_cache.pop(file_path, None)
                    # Trigger repaint for the specific row
                    self.gallery_model.dataChanged.emit(index, index)
                    return

  @pyqtSlot(list)
  def update_selection(self, selected_paths):
    # Selection state changed, trigger viewport update to repaint selection borders
    self.list_view.viewport().update()