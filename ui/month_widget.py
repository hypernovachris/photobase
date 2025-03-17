from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy, QHBoxLayout
from ui.util.flow_layout import FlowLayout
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import os

class MonthWidget(QWidget):
  def __init__(self, text, images):
    super().__init__()
    layout = QVBoxLayout(self)
    label = QLabel(text)
    label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed) 
    layout.addWidget(label)
    
    self.thumbnails_container = QWidget()
    container_layout = FlowLayout()
    container_layout.setSpacing(10)

    # add thumbnail images
    for (thumb_path,) in images:
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
