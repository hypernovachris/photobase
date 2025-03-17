from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class SearchTab(QWidget):
  def __init__(self):
    super().__init__()
    layout = QVBoxLayout()
    layout.addWidget(QLabel("Search goes here"))
    self.setLayout(layout)