from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QListWidget, QPushButton, QGroupBox, QMessageBox, QFrame, QScrollArea, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSlot

class SettingsView(QWidget):
    def __init__(self, settings_controller):
        super().__init__()
        self.settings_controller = settings_controller
        
        self.setup_ui()
        
        # Connect Signals
        # self.settings_controller.themeChanged.connect(self.update_theme_ui)
        self.settings_controller.scanPathsChanged.connect(self.update_paths_ui)
        
        # Initial State
        # self.update_theme_ui()
        self.update_paths_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content_widget = QWidget()
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        content_layout = QVBoxLayout(content_widget)
                
        # Gallery Section
        gallery_group = QGroupBox("Gallery")
        gal_layout = QVBoxLayout()
        gallery_group.setLayout(gal_layout)
        gallery_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        gallery_label = QLabel("Add or remove directories Photobase should scan")
        gal_layout.addWidget(gallery_label)
        
        self.paths_list = QListWidget()
        self.paths_list.setFixedHeight(200)
        gal_layout.addWidget(self.paths_list)
        
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.settings_controller.addPath)
        btn_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self.remove_selected_path)
        btn_layout.addWidget(remove_btn)
        
        btn_layout.addStretch()
        
        apply_btn = QPushButton("Apply Changes")
        apply_btn.clicked.connect(self.settings_controller.applyChanges)
        # Style Apply Button to be prominent?
        btn_layout.addWidget(apply_btn)
        
        gal_layout.addLayout(btn_layout)
        content_layout.addWidget(gallery_group)
        
        # About Section
        about_group = QGroupBox("About")
        about_layout = QHBoxLayout()
        about_group.setLayout(about_layout)
        
        about_btn = QPushButton("About Photobase")
        about_btn.clicked.connect(self.show_about)
        about_layout.addWidget(about_btn)
        about_layout.addStretch()
        
        content_layout.addWidget(about_group)
        content_layout.addStretch()

    @pyqtSlot()
    def update_paths_ui(self):
        self.paths_list.clear()
        self.paths_list.addItems(self.settings_controller.scanPaths)

    def remove_selected_path(self):
        row = self.paths_list.currentRow()
        if row >= 0:
            self.settings_controller.removePath(row)

    def show_about(self):
        QMessageBox.about(self, "Credits & License", 
                          """Photobase Version 0.1.0 by Christopher Doss

Lucide Icons
Copyright © 2024 Lucide Contributors
Licensed under the ISC License.
Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted, provided that the above copyright notice and this permission notice appear in all copies.

"lens" by Side Project, from Noun Project (CC BY 3.0). https://thenounproject.com/icon/lens-8154880/. Icon was modified to change the color to white and remove the text.

Qt Framework
This application uses the Qt Framework under the LGPL v3 license.""")
