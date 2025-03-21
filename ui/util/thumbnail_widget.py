from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

class ThumbnailWidget(QLabel):
  def __init__(self, parent, thumb_path):
    super().__init__(parent)

    self.thumb_path = thumb_path
    self.is_in_view = False

    self.setScaledContents(True)
    self.setFixedSize(128, 128)
    self.setAlignment(Qt.AlignmentFlag.AlignCenter)

  # shouldn't be used since it slows down main thread
  def show_image(self):
    pixmap = QPixmap(self.thumb_path)
    self.setPixmap(pixmap)

  def hide_image(self):
    self.clear()

  def update_visibility(self, vp_top, vp_bottom):
    top = self.mapToGlobal(self.rect().topLeft()).y()
    bottom = self.mapToGlobal(self.rect().bottomLeft()).y()
    
    visibility = bottom >= vp_top and top <= vp_bottom
    if visibility != self.is_in_view:
      self.is_in_view = visibility
      if self.is_in_view:
        self.show_image()
      else:
        self.hide_image()