from PyQt6.QtWidgets import QLabel, QMenu, QStyleOption, QStyle, QFileDialog, QProgressDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QAction, QMouseEvent, QPainter, QColor, QPen
from core.thumbnail_generator import ThumbnailGenerator
from core.gallery_model import GalleryModel
from ui.widgets.tag_edit_dialog import TagEditDialog
import os

class ThumbnailWidget(QLabel):

  THUMBNAIL_SIZE = 128

  def __init__(self, parent, image_path, thumb_path):
    super().__init__(parent)

    self.image_path = image_path
    self.thumb_path = thumb_path
    self.is_in_view = False
    self.index = -1
    self.is_selected = False

    self.setScaledContents(True)
    self.setFixedSize(128, 128)
    self.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self.thumbnail_generator = ThumbnailGenerator.instance()
    self.gallery_model = GalleryModel.instance()

  def show_image(self):
    # check if thumbnail isn't there, if not request it
    if not os.path.exists(self.thumb_path):
      self.thumbnail_generator.request_thumbnail(self.index, self.image_path)
      # draw a gray square
      self.setStyleSheet("background-color: #808080;")
    else:
      pixmap = QPixmap(self.thumb_path)
      self.setPixmap(pixmap)

  def hide_image(self):
    self.clear()

  # we run this when the thumbnail generator tells us it's ready
  def refresh(self):
    self.hide_image()
    if self.is_in_view:
      self.show_image()

  def handle_thumbnail_ready(self):
    if os.path.exists(self.thumb_path):
        self.refresh()

  def retry_load(self):
    if self.is_in_view:
      self.show_image()

  def set_index(self, index):
    self.index = index

  def get_index(self):
    return self.index

  def mousePressEvent(self, event: QMouseEvent):
    if event.button() == Qt.MouseButton.LeftButton:
      modifiers = int(event.modifiers().value)
      self.gallery_model.handle_selection(self.image_path, modifiers)
    elif event.button() == Qt.MouseButton.RightButton:
      if not self.is_selected:
        self.gallery_model.handle_selection(self.image_path, 0)
      # Context menu handled in contextMenuEvent

  def mouseDoubleClickEvent(self, event):
    if event.button() == Qt.MouseButton.LeftButton:
      self.gallery_model.openImageRequested.emit(self.image_path)

  def contextMenuEvent(self, event):
    menu = QMenu(self)
    selected = self.gallery_model.get_selected_paths()
    
    if len(selected) <= 1:
      
      open_action = QAction("Open", self)
      open_action.triggered.connect(lambda: self.gallery_model.openImageRequested.emit(self.image_path))
      menu.addAction(open_action)
    
      reveal_action = QAction("Reveal in File Explorer", self)
      reveal_action.triggered.connect(lambda: self.gallery_model.reveal_file(self.image_path))
      menu.addAction(reveal_action)
    
    # Add Tag / Edit Tags
    if len(selected) <= 1:
      edit_tags_action = QAction("Edit Tags", self)
    else:
      edit_tags_action = QAction("Add Tags", self)
    # Determine if we are editing single or multi
    target = "" # Default multi
    if len(selected) <= 1:
      target = self.image_path
    
    edit_tags_action.triggered.connect(lambda: self.open_tag_dialog(target))
    menu.addAction(edit_tags_action)

    # Remove from current tag filter
    active_filters = self.gallery_model.active_filters
    if len(active_filters) == 1 and active_filters[0].get('type') == 'tag':
        tag_name = active_filters[0].get('value')
        remove_action = QAction(f"Remove from {tag_name}", self)
        remove_action.triggered.connect(lambda: self.gallery_model.remove_tag_from_selection(tag_name))
        menu.addAction(remove_action)
        
    move_action = QAction("Move to...", self)
    move_action.triggered.connect(self.trigger_move)
    menu.addAction(move_action)
    
    menu.exec(event.globalPos())

  def trigger_move(self):
    selected = self.gallery_model.get_selected_paths()
    if not selected:
      selected = [self.image_path]
      
    dest_dir = QFileDialog.getExistingDirectory(self, "Select Destination Directory")
    if not dest_dir:
      return
      
    self.progress_dialog = QProgressDialog("Moving files...", "Cancel", 0, len(selected), self)
    self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
    self.progress_dialog.show()
    
    from ui.widgets.util.move_worker import MoveWorker
    self.worker = MoveWorker(selected, dest_dir)
    
    self.worker.progress.connect(self.progress_dialog.setValue)
    self.worker.fileMoved.connect(self.gallery_model.handle_file_moved)
    self.worker.finished.connect(self.on_move_finished)
    self.worker.start()

  def on_move_finished(self):
    self.progress_dialog.close()
    self.gallery_model.clear_selection()
    self.gallery_model.refresh()

  def open_tag_dialog(self, target):
    dialog = TagEditDialog(target_path=target, parent=self)
    dialog.exec()

  def set_selected(self, selected):
    if self.is_selected != selected:
      self.is_selected = selected
      self.update()



  def paintEvent(self, event):
    super().paintEvent(event)
    
    if self.is_selected:
      painter = QPainter(self)
      pen = QPen(QColor(0, 120, 215))  # Standard Windows selection blue
      pen.setWidth(6) 
      painter.setPen(pen)
      # Draw inside the rect so borders aren't clipped
      painter.drawRect(self.rect().adjusted(3, 3, -3, -3))

  def update_visibility(self, vp_top, vp_bottom):
    top = self.mapToGlobal(self.rect().topLeft()).y()
    bottom = self.mapToGlobal(self.rect().bottomLeft()).y()
    
    visibility = bottom >= vp_top and top <= vp_bottom
    if visibility != self.is_in_view:
      self.is_in_view = visibility
      if self.is_in_view:
        self.refresh()
      else:
        self.hide_image()

  def update_visibility_fast(self, min_y, max_y, container_offset_y):
    # min_y, max_y are in the coordinate space of the main scroll container
    # container_offset_y is the offset of the thumbnails_container (parent of this widget) relative to the main scroll container
    
    my_y = container_offset_y + self.y()
    my_height = self.height()
    
    top = my_y
    bottom = my_y + my_height
    
    visibility = bottom >= min_y and top <= max_y
    
    if visibility != self.is_in_view:
      self.is_in_view = visibility
      if self.is_in_view:
        self.refresh()
      else:
        self.hide_image()