from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QSizePolicy, QSpacerItem
from core.database import db
from PyQt6.QtCore import QTimer
from ui.util.image_group import ImageGroup

#TODO: rethink lazy loading to limit the queue size

def month_numericstr_to_text(numeric_month_str):
  year_str, month_num = tuple(numeric_month_str.split('-'))
  months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
  month_str = months[int(month_num) - 1]
  return month_str + " " + year_str

class GalleryTab(QWidget):
  def __init__(self, parent):
    super().__init__(parent)

    # month widgets, so we can do stuff to them later
    self.month_widgets = []

    # Wait 50ms after scrolling etc. to update
    self.update_timer = QTimer(self)
    self.update_timer.setSingleShot(True)
    self.update_timer.timeout.connect(self.update_months_visibility)

    self.main_layout = QVBoxLayout(self)

    # Scroll Area
    self.scroll_area = QScrollArea(self)
    self.scroll_area.setWidgetResizable(True)
    self.main_layout.addWidget(self.scroll_area)

    # Container for month groups
    self.container = QWidget(self.scroll_area)
    container_layout = QVBoxLayout(self.container)
  
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
      month_widget = ImageGroup(self, month_numericstr_to_text(numeric_month_string), images)
      self.month_widgets.append(month_widget)
      container_layout.addWidget(month_widget)
    db.close()

    container_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

    self.container.setLayout(container_layout)

    self.container.adjustSize()
    self.scroll_area.setWidget(self.container)

    self.scroll_area.verticalScrollBar().valueChanged.connect(self.request_update)
    self.setLayout(self.main_layout)
    self.update_months_visibility()

  def resizeEvent(self, event):
    super().resizeEvent(event)
    self.request_update()

  def request_update(self):
    # set the timer back to zero
    self.update_timer.start(50)

  def update_months_visibility(self):
    
    viewport = self.scroll_area.viewport()
    vp_top = viewport.mapToGlobal(viewport.rect().topLeft()).y()
    vp_bottom = viewport.mapToGlobal(viewport.rect().bottomLeft()).y()

    for month_widget in self.month_widgets:
      month_widget.update_visibility(vp_top, vp_bottom)
