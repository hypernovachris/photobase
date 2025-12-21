from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QFileDialog
from core.config import config
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
