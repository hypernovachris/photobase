from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot, Qt
from PyQt6.QtWidgets import QFileDialog, QApplication, QSplashScreen
from core.config import config
from core.database import db
from core.image_processing import ImageScanner
import json

class SettingsController(QObject):
    scanPathsChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scan_paths = json.loads(config.get("General", "scan_paths", fallback="[]"))

    @pyqtProperty(list, notify=scanPathsChanged)
    def scanPaths(self):
        return self._scan_paths

    @pyqtSlot()
    def addPath(self):
        directory = QFileDialog.getExistingDirectory(None, "Add Directory")
        if directory:
            # Check if directory already exists to avoid duplicates
            if directory not in self._scan_paths:
                self._scan_paths.append(directory)
                self.scanPathsChanged.emit()

    @pyqtSlot(int)
    def removePath(self, index):
        if 0 <= index < len(self._scan_paths):
            del self._scan_paths[index]
            self.scanPathsChanged.emit()

    @pyqtSlot()
    def applyChanges(self):
        config.set("General", "scan_paths", json.dumps(self._scan_paths))
        config.save_config()

        app = QApplication.instance()
        
        # Hide main window(s)
        visible_windows = []
        for window in app.topLevelWindows():
            if window.isVisible():
                visible_windows.append(window)
                window.hide()

        # Show splash screen
        splash = QSplashScreen()
        splash.showMessage("Updating database...", alignment=Qt.AlignmentFlag.AlignCenter)
        splash.show()
        app.processEvents()

        # Update database and thumbnails
        db.connect()
        scanner = ImageScanner()
        scanner.scan_and_update_images(self._scan_paths)
        db.close()
        
        # Refresh gallery if available
        if self.parent() and hasattr(self.parent(), "gallery_model"):
            self.parent().gallery_model.refresh()
            
        # Close splash and restore windows
        splash.close()
        for window in visible_windows:
            window.show()
