from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class PeopleTab(QWidget):
  def __init__(self):
    super().__init__()
    layout = QVBoxLayout()
    layout.addWidget(QLabel("People goes here"))
    self.setLayout(layout)