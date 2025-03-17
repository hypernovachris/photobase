from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy
from ui.util.flow_layout import FlowLayout
from ui.util.thumbnail_widget import ThumbnailWidget

def numeric_to_text(numeric):
  year_str, month_num = tuple(numeric.split('-'))
  months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
  month_str = months[int(month_num) - 1]
  return month_str + " " + year_str


class MonthWidget(QWidget):
  def __init__(self, yearmonth_numeric_str, images=None):
    super().__init__()
    layout = QVBoxLayout(self)
    # whether or not we are in view
    self.is_in_view = False
    # The text (e.g. 'March 2025')
    label = QLabel(numeric_to_text(yearmonth_numeric_str))
    label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed) 
    layout.addWidget(label)
    
    # Widget to hold thumbnails for all images for this month
    self.thumbnails_container = QWidget()
    self.container_layout = FlowLayout()
    self.container_layout.setSpacing(10)
    
    # our list of images, so we can show/hide them @ "runtime" (everything is at runtime but you get the idea)
    self.thumb_widgets = []

    # add all the images for the month into the container
    num_images = len(images)
    for i in range(num_images - 1, -1, -1):
      (thumb_path,) = images[i]
      thumb_widget = ThumbnailWidget(thumb_path)
      thumb_widget.show_image() # FOR NOW - remove this when we implement lazy loading!
      self.container_layout.addWidget(thumb_widget)
      self.thumb_widgets.append(thumb_widget)

    self.thumbnails_container.setLayout(self.container_layout)
    layout.addWidget(self.thumbnails_container)
    self.setLayout(layout)