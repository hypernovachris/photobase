from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy
from ui.widgets.util.flow_layout import FlowLayout
from ui.widgets.util.thumbnail_widget import ThumbnailWidget

class ImageGroup(QWidget):
  def __init__(self, parent, caption, images=None):
    super().__init__(parent)
    layout = QVBoxLayout(self)
    # whether or not we are in view
    self.is_in_view = False
    self.partially_obscured = False
    # The text (e.g. 'March 2025')
    label = QLabel(caption, self)
    label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed) 
    layout.addWidget(label)
    
    # Widget to hold thumbnails for all images for this month
    self.thumbnails_container = QWidget(self)
    self.container_layout = FlowLayout(self.thumbnails_container)
    self.container_layout.setSpacing(10)
    
    # our list of images, so we can show/hide them @ "runtime" (everything is at runtime but you get the idea)
    self.thumb_widgets = []

    # add all the images for the month into the container
    for (image_path, thumb_path) in images:
      thumb_widget = ThumbnailWidget(self.thumbnails_container, image_path, thumb_path)
      self.container_layout.addWidget(thumb_widget)
      self.thumb_widgets.append(thumb_widget)

    self.thumbnails_container.setLayout(self.container_layout)
    layout.addWidget(self.thumbnails_container)
    self.setLayout(layout)

  def update_visibility(self, min_y, max_y):
    # Use local coordinates relative to the parent container
    my_y = self.y()
    my_height = self.height()
    
    top = my_y
    bottom = my_y + my_height
    
    visibility = bottom >= min_y and top <= max_y
    # simple check: if I am fully above min_y or fully below max_y, I am NOT in view
    # "partially obscured" logic:
    # completely visible = top >= min_y and bottom <= max_y
    fully_visible = top >= min_y and bottom <= max_y
    partially_obscured = not fully_visible
    
    if visibility != self.is_in_view or partially_obscured != self.partially_obscured:
      self.is_in_view = visibility
      self.partially_obscured = partially_obscured
      
      container_offset_y = my_y + self.thumbnails_container.y()
      self._update_children_visibility(min_y, max_y, container_offset_y)
    elif self.is_in_view:
      container_offset_y = my_y + self.thumbnails_container.y()
      self._update_children_visibility(min_y, max_y, container_offset_y)

  def _update_children_visibility(self, min_y, max_y, container_offset_y):
    if not self.thumb_widgets:
        return
        
    width = self.thumbnails_container.width()
    spacing = 10
    thumb_width = ThumbnailWidget.THUMBNAIL_SIZE
    col_width = thumb_width + spacing
    cols = max(1, (width + spacing) // col_width)
    
    for r in range(0, len(self.thumb_widgets), cols):
        row_widgets = self.thumb_widgets[r : r + cols]
        if not row_widgets:
            continue
            
        first_widget = row_widgets[0]
        y_coord = first_widget.y()
        height = first_widget.height()
        
        top = container_offset_y + y_coord
        bottom = top + height
        row_in_view = bottom >= min_y and top <= max_y
        
        for widget in row_widgets:
            if row_in_view != widget.is_in_view:
                widget.is_in_view = row_in_view
                if row_in_view:
                    widget.refresh()
                else:
                    widget.hide_image()

  def retry_load(self):
    if self.is_in_view:
      for thumb_widget in self.thumb_widgets:
        thumb_widget.retry_load()

  def get_thumb_widgets(self):
    return self.thumb_widgets