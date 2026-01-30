from core.config import config
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtQml import QQmlApplicationEngine
from core.database import db
from core.image_processing import ImageScanner
import os

os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"
from core.gallery_model import GalleryModel
from core.settings_controller import SettingsController
import json
import sys
import os

def initialize_app(scan_paths):
  db.connect()
  scanner = ImageScanner()
  scanner.scan_and_update_images(scan_paths)
  db.close()

if __name__ == "__main__":
  # update the database if necessary
  scan_paths = json.loads(config.get("General", "scan_paths", fallback="[]"))

  os.makedirs("thumbnails", exist_ok=True)

  app = QApplication(sys.argv)
  
  # show a splash screen
  splash = QSplashScreen()
  splash.showMessage("Updating database...", alignment=Qt.AlignmentFlag.AlignCenter)
  splash.show()
  
  # Process events to show splash immediately
  app.processEvents()

  initialize_app(scan_paths)

  from core.gallery_model import GalleryModel
  from core.thumbnail_generator import ThumbnailGenerator
  from core.settings_controller import SettingsController
  from core.heic_provider import HeicImageProvider
  from ui.widgets.main_window import MainWindow

  # Initialize Controllers
  gallery_model = GalleryModel()
  settings_controller = SettingsController()
  thumbnail_generator = ThumbnailGenerator()
  heic_provider = HeicImageProvider()

  # Pass 'app' if needed by controllers (e.g. for parenting or signals if they expect QObject parent)
  # The original code passed 'app' to some controllers. Let's check constructor signatures if possible, 
  # but based on my earlier read, GalleryModel(parent=None) was default. 
  # However, to be safe and consistent with previous code where they were parented to app:
  gallery_model.setParent(app)
  settings_controller.setParent(app)
  thumbnail_generator.setParent(app)
  
  # Initialize Main Window
  window = MainWindow(gallery_model, thumbnail_generator, settings_controller, heic_provider)
  window.show()

  # Close splash screen
  splash.close()

  sys.exit(app.exec())