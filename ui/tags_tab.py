from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class TagsTab(QWidget):
  def __init__(self, parent):
    super().__init__(parent)
    layout = QVBoxLayout(self)
    layout.addWidget(QLabel("Tags goes here", self))
    self.setLayout(layout)