from PyQt6.QtWidgets import QWidget, QLayout, QVBoxLayout, QScrollArea, QSizePolicy, QSpacerItem, QAbstractScrollArea
from core.database import db
from ui.month_widget import MonthWidget

class GalleryTab(QWidget):
  def __init__(self):
    super().__init__()

    self.layout = QVBoxLayout(self)

    # month widgets, so we can do stuff to them later
    self.month_widgets = []

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
      month_widget = MonthWidget(numeric_month_string, images)
      self.month_widgets.append(month_widget)
      container_layout.addWidget(month_widget)
    db.close()

    container_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

    self.container.setLayout(container_layout)

    self.container.adjustSize()
    self.scroll_area.setWidget(self.container)

    self.setLayout(self.layout) 