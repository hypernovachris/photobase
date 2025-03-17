from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class PlacesTab(QWidget):
  def __init__(self):
    super().__init__()
    layout = QVBoxLayout()
    layout.addWidget(QLabel("Places goes here"))
    self.setLayout(layout)