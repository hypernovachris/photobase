from core.config import config
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtCore import Qt, QUrl
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
  
  app = QApplication(sys.argv)
  
  # show a splash screen
  splash = QSplashScreen()
  splash.showMessage("Updating database...", alignment=Qt.AlignmentFlag.AlignCenter)
  splash.show()
  
  # Process events to show splash immediately
  app.processEvents()
  
  initialize_app(scan_paths)
  
  engine = QQmlApplicationEngine()
  
  from core.thumbnail_generator import ThumbnailGenerator
  
  # Keep references to prevent garbage collection
  # Although they are in local scope of a blocking function, explicit references can help debug or edge cases
  app.gallery_model = GalleryModel(app)
  engine.rootContext().setContextProperty("galleryModel", app.gallery_model)

  app.settingsController = SettingsController(app)
  engine.rootContext().setContextProperty("settingsController", app.settingsController)
  
  app.thumbnailGenerator = ThumbnailGenerator(app)
  engine.rootContext().setContextProperty("thumbnailGenerator", app.thumbnailGenerator)
  
  print("SettingsController initialized and registered")
  
  # Load main.qml
  current_dir = os.path.dirname(os.path.abspath(__file__))
  qml_file = os.path.join(current_dir, "ui/main.qml")
  engine.load(QUrl.fromLocalFile(qml_file))
  
  # Check if QML loaded successfully
  if not engine.rootObjects():
      sys.exit(-1)
      
  # Close splash screen
  splash.close()
  
  sys.exit(app.exec())