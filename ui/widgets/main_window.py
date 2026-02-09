from PyQt6.QtWidgets import QMainWindow, QTabWidget, QStackedWidget
from PyQt6.QtCore import pyqtSlot
from ui.widgets.gallery_view import GalleryView
from ui.widgets.search_view import SearchView
from ui.widgets.settings_view import SettingsView
from ui.widgets.tags_view import TagsView
from ui.widgets.image_viewer import ImageViewer
from core.gallery_model import GalleryModel

class MainWindow(QMainWindow):
    def __init__(self, settings_controller, heic_provider):
        super().__init__()
        
        self.setWindowTitle("Photobase")
        self.resize(1200, 800)
        
        # Keep references to controllers
        self.gallery_model = GalleryModel.instance()
        self.settings_controller = settings_controller
        self.heic_provider = heic_provider

        # Setup Central Widget (Stack)
        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)
        
        # Page 0: Main Tabs
        self.tabs = QTabWidget()
        self.central_stack.addWidget(self.tabs)
        
        # Create Views
        # Pass self as parent/controller for navigation
        self.gallery_view = GalleryView(self)
        self.tags_view = TagsView(self)
        self.search_view = SearchView(self)
        self.settings_view = SettingsView(self.settings_controller)
        
        # Add Tabs
        self.tabs.addTab(self.gallery_view, "Gallery")
        self.tabs.addTab(self.tags_view, "Tags")
        self.tabs.addTab(self.search_view, "Search")
        self.tabs.addTab(self.settings_view, "Settings")
        
        # Page 1: Image Viewer
        self.image_viewer = ImageViewer(self)
        self.image_viewer.closeRequested.connect(self.close_viewer)
        self.central_stack.addWidget(self.image_viewer)
        
        # Connect Signals from Model for Navigation
        self.gallery_model.openImageRequested.connect(self.open_image)
        self.gallery_model.switchGalleryRequested.connect(self.switch_to_gallery)

    @pyqtSlot(str)
    def open_image(self, path):
        self.image_viewer.open(path)
        self.central_stack.setCurrentIndex(1)

    @pyqtSlot()
    def close_viewer(self):
        self.central_stack.setCurrentIndex(0)

    @pyqtSlot()
    def switch_to_gallery(self):
        self.central_stack.setCurrentIndex(0)
        self.tabs.setCurrentIndex(0) # Gallery Tab
