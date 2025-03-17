from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy, QHBoxLayout
from ui.util.flow_layout import FlowLayout
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import os

def numeric_to_text(numeric):
  year_str, month_num = tuple(numeric.split('-'))
  months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
  month_str = months[int(month_num) - 1]
  return month_str + " " + year_str


class MonthWidget(QWidget):
  def __init__(self, yearmonth_numeric_str, images):
    super().__init__()
    layout = QVBoxLayout(self)
    label = QLabel(numeric_to_text(yearmonth_numeric_str))
    label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed) 
    layout.addWidget(label)
    
    self.thumbnails_container = QWidget()
    container_layout = FlowLayout()
    container_layout.setSpacing(10)

    num_images = len(images)
    for i in range(num_images - 1, -1, -1):
      (thumb_path,) = images[i]
      if os.path.exists(thumb_path):
        pixmap = QPixmap(thumb_path)
        label = QLabel(self)
        label.setPixmap(pixmap)
        label.setScaledContents(True)
        label.setFixedSize(128, 128)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(label)

    self.thumbnails_container.setLayout(container_layout)

    layout.addWidget(self.thumbnails_container)
    self.setLayout(layout)
