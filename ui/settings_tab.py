from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QScrollArea, QSizePolicy, QSpacerItem, QLabel, QListView, QFileDialog
from PyQt6.QtCore import QStringListModel
from ui.util.right_justified_button_bar import RightJustifiedButtonBar
from abc import ABC, abstractmethod
from core.config import config
import json

class Setting(QWidget):
  @abstractmethod
  def apply_changes(self):
    pass

class DirectoryListEditor(Setting):
  def __init__(self):
    super().__init__()

    # the layout
    self.main_layout = QVBoxLayout()

    # load in data from the config, keep track so can be saved later
    self.scan_paths = json.loads(config.get("General", "scan_paths", fallback="[]"))
    

    # label
    self.label = QLabel("Add or remove directories Photobase should scan:")
    self.main_layout.addWidget(self.label)

    # model/view
    self.model = QStringListModel()
    self.view = QListView()
    self.model.setStringList(self.scan_paths)
    self.view.setModel(self.model)
    self.view.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
    self.view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    self.main_layout.addWidget(self.view)

    # bottom buttons
    self.button_bar = RightJustifiedButtonBar()
    self.add_button = self.button_bar.add_button(QPushButton("Add"))
    self.add_button.clicked.connect(self.add_directory)
    self.remove_button = self.button_bar.add_button(QPushButton("Remove"))
    self.remove_button.clicked.connect(self.remove_directory)
    self.main_layout.addWidget(self.button_bar)

    self.setLayout(self.main_layout)

  def add_directory(self):
    directory = QFileDialog.getExistingDirectory(None, "Add Directory")
    if directory:
      self.scan_paths.append(directory)
      self.model.setStringList(self.scan_paths)

  # removes the selected directory(ies)
  def remove_directory(self):
    model_indices = self.view.selectedIndexes()
    indices = [i.row() for i in model_indices]
    for index in sorted(indices, reverse=True):
      del self.scan_paths[index]
    self.model.setStringList(self.scan_paths)

    

  def apply_changes(self):
    config.set("General", "scan_paths", json.dumps(self.scan_paths))
    config.save_config()

    


class SettingsPage(QWidget):
  def __init__(self):
    super().__init__()
    self.settings = []
    self.main_layout = QVBoxLayout()

    # adding the settings
    self.add_setting(DirectoryListEditor())

    self.main_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

    self.setLayout(self.main_layout)

  def add_setting(self, setting):
    self.main_layout.addWidget(setting)
    self.settings.append(setting)

  def apply_changes(self):
    for setting in self.settings:
      setting.apply_changes()


class SettingsTab(QWidget):
  def __init__(self, parent):
    super().__init__(parent)

    self.main_layout = QVBoxLayout(self)
    self.main_layout.setSpacing(0)

    self.scroll_area = QScrollArea(self)
    self.scroll_area.setWidgetResizable(True)
    self.main_layout.addWidget(self.scroll_area)

    self.settings_page = SettingsPage()
    self.scroll_area.setWidget(self.settings_page)

    self.button_bar = RightJustifiedButtonBar()
    self.apply_button = self.button_bar.add_button(QPushButton("Apply Changes"))
    self.apply_button.clicked.connect(self.settings_page.apply_changes)
    #self.button_bar.setFrameShape(QFrame.Shape.Box)
    self.main_layout.addWidget(self.button_bar)
    
    self.setLayout(self.main_layout)