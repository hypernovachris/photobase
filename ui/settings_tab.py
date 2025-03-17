from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class SettingsTab(QWidget):
  def __init__(self):
    super().__init__()
    layout = QVBoxLayout()
    layout.addWidget(QLabel("Settings goes here"))
    self.setLayout(layout)