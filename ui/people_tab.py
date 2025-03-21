from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class PeopleTab(QWidget):
  def __init__(self, parent):
    super().__init__(parent)
    layout = QVBoxLayout(self)
    layout.addWidget(QLabel("People goes here", self))
    self.setLayout(layout)