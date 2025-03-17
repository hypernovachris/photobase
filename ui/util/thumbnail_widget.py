from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import os

class ThumbnailWidget(QLabel):
  def __init__(self, thumb_path):
    super().__init__()
    self.thumb_path = thumb_path
    self.setScaledContents(True)
    self.setFixedSize(128, 128)
    self.setAlignment(Qt.AlignmentFlag.AlignCenter)

  def show_image(self):
    if os.path.exists(self.thumb_path):
      pixmap = QPixmap(self.thumb_path)
      self.setPixmap(pixmap)

  def hide_image(self):
    self.setPixmap(QPixmap())