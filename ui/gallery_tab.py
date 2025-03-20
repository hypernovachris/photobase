from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QSizePolicy, QSpacerItem
from core.database import db
from core.image_loader import ImageLoaderThread
from PyQt6.QtCore import QTimer
from ui.util.image_group import ImageGroup
import queue

def month_numericstr_to_text(numeric_month_str):
  year_str, month_num = tuple(numeric_month_str.split('-'))
  months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
  month_str = months[int(month_num) - 1]
  return month_str + " " + year_str

class GalleryTab(QWidget):
  def __init__(self):
    super().__init__()

    # month widgets, so we can do stuff to them later
    self.month_widgets = []

    # queues
    self.task_queue = queue.Queue()
    self.result_queue = queue.Queue()

    # background loading thread
    self.loader_thread = ImageLoaderThread(self.task_queue, self.result_queue)
    self.loader_thread.start()

    self.update_timer = QTimer()
    self.update_timer.timeout.connect(self.process_results)
    self.update_timer.start(50)

    self.layout = QVBoxLayout(self)

    # Scroll Area
    self.scroll_area = QScrollArea(self)
    self.scroll_area.setWidgetResizable(True)
    self.layout.addWidget(self.scroll_area)

    # Scroll area container
    self.container = QWidget()
    container_layout = QVBoxLayout()
  
    db.connect()
    db.cursor.execute("SELECT DISTINCT strftime('%Y-%m', datetime(last_modified, 'unixepoch')) AS month FROM images ORDER BY month DESC;")
    numeric_month_strings = db.cursor.fetchall()
    for (numeric_month_string,) in numeric_month_strings:
      db.cursor.execute("""
        SELECT thumbnail_path FROM images
        WHERE strftime('%Y-%m', datetime(last_modified, 'unixepoch')) = ?
        ORDER BY last_modified ASC
      """, (numeric_month_string,))
      images = db.cursor.fetchall()
      month_widget = ImageGroup(month_numericstr_to_text(numeric_month_string), self.task_queue, images)
      self.month_widgets.append(month_widget)
      container_layout.addWidget(month_widget)
    db.close()

    container_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

    self.container.setLayout(container_layout)

    self.container.adjustSize()
    self.scroll_area.setWidget(self.container)

    self.scroll_area.verticalScrollBar().valueChanged.connect(self.update_months_visibility)
    self.setLayout(self.layout)
    self.update_months_visibility()

  def resizeEvent(self, event):
    super().resizeEvent(event)
    self.update_months_visibility()


  def process_results(self):
    while not self.result_queue.empty():
      label, pixmap = self.result_queue.get()
      if pixmap:
        label.setPixmap(pixmap)
      else:
        label.clear()

  def update_months_visibility(self):
    viewport = self.scroll_area.viewport()
    vp_top = viewport.mapToGlobal(viewport.rect().topLeft()).y()
    vp_bottom = viewport.mapToGlobal(viewport.rect().bottomLeft()).y()

    for month_widget in self.month_widgets:
      month_widget.update_visibility(vp_top, vp_bottom)

    with self.loader_thread.condition:
      self.loader_thread.condition.notify()

  def kill_loader_thread(self):
    self.loader_thread.stop()
    self.loader_thread.join()