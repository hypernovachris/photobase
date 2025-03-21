from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from ui.gallery_tab import GalleryTab
from ui.tags_tab import TagsTab
from ui.people_tab import PeopleTab
from ui.places_tab import PlacesTab
from ui.search_tab import SearchTab
from ui.settings_tab import SettingsTab

class MainWindow(QMainWindow):
  def __init__(self):
    super().__init__()
    self.setWindowTitle("Photobase")
    self.setGeometry(100, 100, 1000, 700)

    # tab widget
    self.tabs = QTabWidget(self)
    self.setCentralWidget(self.tabs)

    # add tabs
    self.gallery_tab = GalleryTab(self)
    self.tabs.addTab(self.gallery_tab, "Gallery")
    self.tabs.addTab(TagsTab(self), "Tags")
    self.tabs.addTab(PeopleTab(self), "People")
    self.tabs.addTab(PlacesTab(self), "Places")
    self.tabs.addTab(SearchTab(self), "Search")
    self.tabs.addTab(SettingsTab(self), "Settings")