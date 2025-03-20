from core.config import config
from ui.main_window import MainWindow
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtCore import Qt
from core.database import db
from core.image_processing import ImageScanner
import json

def initialize_app(scan_paths):
  db.connect()
  scanner = ImageScanner()
  scanner.scan_and_update_images(scan_paths)
  db.close()


if __name__ == "__main__":
  # update the database if necessary
  scan_paths = json.loads(config.get("General", "scan_paths", fallback="[]"))
  # show a splash screen
  app = QApplication([])
  splash = QSplashScreen()
  splash.showMessage("Updating database...", alignment=Qt.AlignmentFlag.AlignCenter)
  splash.show()
  initialize_app(scan_paths)
  # start the ui
  window = MainWindow()
  window.show()
  splash.finish(window)
  app.aboutToQuit.connect(window.cleanup)
  app.exec()