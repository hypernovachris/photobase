from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class TagsTab(QWidget):
  def __init__(self):
    super().__init__()
    layout = QVBoxLayout()
    layout.addWidget(QLabel("Tags goes here"))
    self.setLayout(layout)