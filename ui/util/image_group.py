from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy
from ui.util.flow_layout import FlowLayout
from ui.util.thumbnail_widget import ThumbnailWidget

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
    num_images = len(images)
    for i in range(num_images - 1, -1, -1):
      (thumb_path,) = images[i]
      thumb_widget = ThumbnailWidget(self.thumbnails_container, thumb_path)
      #thumb_widget.show_image() # FOR NOW - remove this when we implement lazy loading!
      self.container_layout.addWidget(thumb_widget)
      self.thumb_widgets.append(thumb_widget)

    self.thumbnails_container.setLayout(self.container_layout)
    layout.addWidget(self.thumbnails_container)
    self.setLayout(layout)

  def update_visibility(self, vp_top, vp_bottom):
    top = self.mapToGlobal(self.rect().topLeft()).y()
    bottom = self.mapToGlobal(self.rect().bottomLeft()).y()
    
    visibility = bottom >= vp_top and top <= vp_bottom
    partially_obscured = not (bottom <= vp_bottom and top >= vp_top)
    if visibility != self.is_in_view or partially_obscured != self.partially_obscured or partially_obscured:
      self.is_in_view, self.partially_obscured = visibility, partially_obscured
      for thumb_widget in self.thumb_widgets:
        thumb_widget.update_visibility(vp_top, vp_bottom)

#TODO: We can skip updating EVERY image by using the fact that only an entire row can become visible at a time!