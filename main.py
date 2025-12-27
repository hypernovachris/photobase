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
from core.face_scanner import FaceScanner
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
  
  app.faceScanner = FaceScanner(app)
  engine.rootContext().setContextProperty("faceScanner", app.faceScanner)
  app.faceScanner.start_scan()
  
  app.aboutToQuit.connect(app.faceScanner.stop_scan)
  
  # print("SettingsController initialized and registered")
  
  # Load main.qml
  current_dir = os.path.dirname(os.path.abspath(__file__))

  # Instantiate Theme and register as context property
  from PyQt6.QtQml import QQmlComponent, QQmlEngine
  theme_component = QQmlComponent(engine, QUrl.fromLocalFile(os.path.join(current_dir, "ui/Theme.qml")))
  theme_object = theme_component.create()
  if not theme_object:
      print("Error creating theme object:", theme_component.errors())
      sys.exit(-1)

  # Set parent to app and ownership to Cpp to prevent GC by QML engine
  theme_object.setParent(app)
  QQmlEngine.setObjectOwnership(theme_object, QQmlEngine.ObjectOwnership.CppOwnership)
      
  engine.rootContext().setContextProperty("theme", theme_object)
  
  # Keep reference to prevent GC (App parent might be enough, but this doesn't hurt)
  app.theme_object = theme_object

  qml_file = os.path.join(current_dir, "ui/main.qml")
  engine.load(QUrl.fromLocalFile(qml_file))
  
  # Check if QML loaded successfully
  if not engine.rootObjects():
      sys.exit(-1)
      
  # Close splash screen
  splash.close()
  
  sys.exit(app.exec())