import configparser
import os
from PyQt6.QtWidgets import QMessageBox, QFileDialog
import json

CONFIG_FILE = "./config.txt"

class ConfigManager:
  def __init__(self):
    self.config = configparser.ConfigParser()
    self.load_config()

  def load_config(self):
    if os.path.exists(CONFIG_FILE):
      self.config.read(CONFIG_FILE)
    else:
      self.set_defaults()
      self.save_config()

  def set_defaults(self):
    from PyQt6.QtWidgets import QApplication

    app = QApplication([])

    # show message box
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Information)
    msg.setWindowTitle("Select Image Directory")
    msg.setText("Please select a directory Photobase will scan for images. You can add more or change these later.")
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.exec()

    directory = QFileDialog.getExistingDirectory(None, "Select Directory to Scan")
    scan_paths = [directory] if directory else []

    #Set default values
    self.config["General"] = {
      "scan_paths": json.dumps(scan_paths)
    }

    self.save_config()
  
  def save_config(self):
    with open(CONFIG_FILE, "w") as configfile:
      self.config.write(configfile)
  
  def get(self, section, key, fallback=None):
    return self.config.get(section, key, fallback=fallback)

  def getboolean(self, section, key, fallback=None):
    return self.config.getboolean(section, key, fallback=fallback)
  
  def set(self, section, key, value):
    if section not in self.config:
      self.config[section] = {}
    self.config[section][key] = value
    self.save_config()
  
config = ConfigManager()