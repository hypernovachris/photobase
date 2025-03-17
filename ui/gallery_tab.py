from PyQt6.QtWidgets import QWidget, QLayout, QVBoxLayout, QScrollArea, QSizePolicy, QSpacerItem, QAbstractScrollArea
from core.database import db
from ui.month_widget import MonthWidget

class GalleryTab(QWidget):
  def __init__(self):
    super().__init__()

    self.layout = QVBoxLayout(self)

    # Scroll Area
    self.scroll_area = QScrollArea(self)
    self.scroll_area.setWidgetResizable(True)
    self.layout.addWidget(self.scroll_area)

    # Scroll area container
    self.container = QWidget()
    container_layout = QVBoxLayout()
    

    # for now just get all the images
    db.connect()
    db.cursor.execute("SELECT thumbnail_path FROM images")
    images = db.cursor.fetchall()
    db.close()

    for label in ["March 2025", "October 2024", "September 2024", "June 2024", "May 2024", "January 2024"]:
      month_widget = MonthWidget(label, images)
      container_layout.addWidget(month_widget)

    container_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

    self.container.setLayout(container_layout)

    self.container.adjustSize()
    self.scroll_area.setWidget(self.container)

    self.setLayout(self.layout) 