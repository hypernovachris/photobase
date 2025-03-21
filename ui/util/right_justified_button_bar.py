from PyQt6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QSpacerItem, QSizePolicy
from PyQt6.QtCore import Qt

class RightJustifiedButtonBar(QFrame):
  def __init__(self):
    super().__init__()
    self.main_layout = QHBoxLayout(self)
    self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    self.main_layout.setSpacing(0)
    self.main_layout.setContentsMargins(0, 0, 0, 0)
    self.main_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

  def add_button(self, button: QPushButton):
    self.main_layout.addWidget(button)
    return button