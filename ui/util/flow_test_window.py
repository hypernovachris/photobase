import sys
from PyQt6.QtWidgets import QApplication, QPushButton, QWidget
from flow_layout import FlowLayout

class Window(QWidget):
  def __init__(self):
    super().__init__()

    flow_layout = FlowLayout(self)
    flow_layout.addWidget(QPushButton("Short"))
    flow_layout.addWidget(QPushButton("Longer"))
    flow_layout.addWidget(QPushButton("Different Text"))
    flow_layout.addWidget(QPushButton("More text"))
    flow_layout.addWidget(QPushButton("Even longer button text"))

    self.setWindowTitle("Flow Layout")

if __name__ == "__main__":
  app = QApplication(sys.argv)
  main_win = Window()
  main_win.show()
  sys.exit(app.exec())