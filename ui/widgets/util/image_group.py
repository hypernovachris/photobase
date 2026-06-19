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
    
    # If visibility state changed, OR if we haven't checked children yet (e.g. first run), we must update children
    # Actually, if we are NOT visible, we don't strictly need to update children to "not visible" if they already are?
    # But if we go from visible -> not visible, we must update children.
    # If we go from not visible -> visible, we must update children.
    # The only case we can skip is: not visible -> not visible.
    
    # Check if this is the first update? no easy way.
    # But wait, self.is_in_view initializes to False.
    # If we are effectively "not in view" (scrolled way down), we want to stay False.
    # But if we were PREVIOUSLY in view, `self.is_in_view` would be True.
    
    # The issue: When clearing filters, we recreate ImageGroups. They start as `False` (not in view).
    # `populate_view` creates them. `update_months_visibility` runs.
    # If they are in view, `visibility` is True. `visibility != self.is_in_view` is True. We update children.
    # If they are NOT in view, `visibility` is False. `visibility != self.is_in_view` is False.
    # We RETURN early. Children are never told anything.
    # Children initialize with `is_in_view = False`.
    # So ... this logic seems correct for "not visible".
    
    # However, `partially_obscured` change also triggers update.
    
    # Why are thumbnails not loading then?
    # Maybe `min_y`/`max_y` are wrong?
    
    if visibility != self.is_in_view or partially_obscured != self.partially_obscured:
      self.is_in_view = visibility
      self.partially_obscured = partially_obscured
      
      # Determine offset for children once
      # self.thumbnails_container is a child of self
      container_offset_y = my_y + self.thumbnails_container.y()

      for thumb_widget in self.thumb_widgets:
        thumb_widget.update_visibility_fast(min_y, max_y, container_offset_y)
    elif self.is_in_view:
        # Optimization: If we are still in view (state didn't change), we STILL might need to update children
        # because the scroll position CHANGED, so some children might have moved in/out of view!
        # This was the bug! We were skipping child updates just because the GROUP remained "in view".
        
        container_offset_y = my_y + self.thumbnails_container.y()
        for thumb_widget in self.thumb_widgets:
            thumb_widget.update_visibility_fast(min_y, max_y, container_offset_y)

  def retry_load(self):
    if self.is_in_view:
      for thumb_widget in self.thumb_widgets:
        thumb_widget.retry_load()

  def get_thumb_widgets(self):
    return self.thumb_widgets

#TODO: We can skip updating EVERY image by using the fact that only an entire row can become visible at a time!