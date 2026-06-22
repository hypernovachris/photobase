from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QSizePolicy, QSpacerItem, QHBoxLayout, QLabel, QPushButton
from core.database import db
from PyQt6.QtCore import QTimer, Qt
from ui.widgets.util.image_group import ImageGroup
from PyQt6.QtCore import pyqtSlot
from core.gallery_model import GalleryModel
from core.thumbnail_generator import ThumbnailGenerator
from ui.widgets.util.thumbnail_widget import ThumbnailWidget
from core.profiler import profile, ProfileTimer


class GalleryView(QWidget):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.gallery_model = GalleryModel.instance()
    self.thumbnail_generator = ThumbnailGenerator.instance()
    self.thumbnail_generator.thumbnailReady.connect(self.on_thumbnail_ready)
    self.thumbnail_generator.queueEmpty.connect(self.on_queue_empty)
    self.gallery_model.selectionChanged.connect(self.update_selection)
    
    # Reload view when model changes (e.g. filters applied)
    self.gallery_model.countChanged.connect(self.populate_view)
    self.gallery_model.filterChanged.connect(self.update_banner)

    # month widgets, so we can do stuff to them later
    self.month_widgets = []
    # references to all thumbnail widgets, so we can update them when a thumbnail is ready
    self.all_thumb_widgets = []

    # Wait 50ms after scrolling etc. to update
    self.update_timer = QTimer(self)
    self.update_timer.setSingleShot(True)
    self.update_timer.timeout.connect(self.update_months_visibility)

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

    # Scroll Area
    self.scroll_area = QScrollArea(self)
    self.scroll_area.setWidgetResizable(True)
    self.main_layout.addWidget(self.scroll_area)

    # Container for month groups
    self.container = QWidget(self.scroll_area)
    self.container_layout = QVBoxLayout(self.container)
    
    self.container.setLayout(self.container_layout)
    self.scroll_area.setWidget(self.container)

    self.scroll_area.verticalScrollBar().valueChanged.connect(self.request_update)
    self.setLayout(self.main_layout)
    
    # Initial Population
    self.populate_view()

  def resizeEvent(self, event):
    super().resizeEvent(event)
    self.request_update()

  def request_update(self):
    # set the timer back to zero
    self.update_timer.start(50)
    
  @pyqtSlot()
  @profile
  def populate_view(self):
    # Clear existing
    for widget in self.month_widgets:
        widget.deleteLater()
    self.month_widgets = []
    self.all_thumb_widgets = []
    
    # Remove spacers/items from layout
    while self.container_layout.count():
        child = self.container_layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()
        elif child.spacerItem():
            self.container_layout.removeItem(child)
            
    # Re-populate using Model data
    sections = self.gallery_model._sections 
    
    with ProfileTimer("populate_view widget creation loop"):
        for section in sections:
            month_text = section['month_text']
            
            # Adapt model images (dict) to ImageGroup expectation (path, thumbnail)
            model_images = section['images']
            adapted_images = [(img['path'], img['thumbnailPath']) for img in model_images]
            
            month_widget = ImageGroup(self.container, month_text, adapted_images)
            self.month_widgets.append(month_widget)
            self.all_thumb_widgets.extend(month_widget.get_thumb_widgets())
            self.container_layout.addWidget(month_widget)

    with ProfileTimer("populate_view indices loop"):
      # set the indices for all thumbnail widgets
      for i in range(len(self.all_thumb_widgets)):
        self.all_thumb_widgets[i].set_index(i)

    self.container_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
    # Important: adjustSize helps with scroll area
    self.container.adjustSize()
    
    # Update visibility after layout is settled
    # Use QTimer to defer execution until after layout calculations are complete
    QTimer.singleShot(0, self.update_months_visibility)
    
    # Update Banner Visualization based on current model state
    self.update_banner(self.gallery_model.get_active_filter())

  @pyqtSlot(str)
  def update_banner(self, filter_name):
      if filter_name:
          self.banner_label.setText(f"Filtering by: {filter_name}")
          self.banner_container.setVisible(True)
      else:
          self.banner_container.setVisible(False)

  @profile
  def update_months_visibility(self):

    # we need to calculate how many thumbnails could possibly be visible, to tell the thumbnail generator what its max queue size should be.
    # crude way to do this: viewport dimensions / thumbnail dimensions
    if ThumbnailWidget.THUMBNAIL_SIZE > 0:
        num_thumbs_x = self.scroll_area.viewport().width() // ThumbnailWidget.THUMBNAIL_SIZE
        num_thumbs_y = self.scroll_area.viewport().height() // ThumbnailWidget.THUMBNAIL_SIZE + 1
        num_thumbs_total = num_thumbs_x * num_thumbs_y
        self.thumbnail_generator.setMaxQueueSize(num_thumbs_total)
    
    # since we assume the view has changed, we will tell the thumbnail generator to clear its queue
    self.thumbnail_generator.clearQueue()
    
    # Use Container-relative coordinates (much faster)
    # The container is the widget inside the scroll area.
    # The scrollbar value tells us how far down the viewport is.
    min_y = self.scroll_area.verticalScrollBar().value()
    viewport_height = self.scroll_area.viewport().height()
    max_y = min_y + viewport_height

    for month_widget in self.month_widgets:
        month_widget.update_visibility(min_y, max_y)
  
  @pyqtSlot(int)
  def on_thumbnail_ready(self, index):
    if 0 <= index < len(self.all_thumb_widgets):
        self.all_thumb_widgets[index].handle_thumbnail_ready()

  @pyqtSlot()
  def on_queue_empty(self):
      # Wait a bit then re-check visibility to catch any missed thumbnails
      # QTimer.singleShot(250, self.update_months_visibility)
      # Force check for visible items without full visibility recalc
      for month_widget in self.month_widgets:
          month_widget.retry_load()

  @pyqtSlot(list)
  def update_selection(self, selected_paths):
    sel_set = set(selected_paths)
    for tw in self.all_thumb_widgets:
        tw.set_selected(tw.image_path in sel_set)