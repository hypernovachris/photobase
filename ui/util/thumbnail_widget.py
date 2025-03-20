from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt

class ThumbnailWidget(QLabel):
  def __init__(self, thumb_path, task_queue):
    super().__init__()

    self.thumb_path = thumb_path
    self.task_queue = task_queue
    self.is_in_view = False

    self.setScaledContents(True)
    self.setFixedSize(128, 128)
    self.setAlignment(Qt.AlignmentFlag.AlignCenter)

  # shouldn't be used since it slows down main thread
  def show_image(self):
    self.task_queue.put(("load", self))

  def hide_image(self):
    self.task_queue.put(("unload", self))

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