from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QListWidget, QDialogButtonBox, QCheckBox, 
    QListWidgetItem, QWidget
)
from PyQt6.QtCore import Qt, pyqtSlot, QSize
from core.gallery_model import GalleryModel

class TagEditDialog(QDialog):
    def __init__(self, target_path="", parent=None, add_tags=False):
        super().__init__(parent)
        self.gallery_model = GalleryModel.instance()
        self.target_path = target_path
        self.is_add_mode = (target_path == "") or add_tags # Empty path means operating on selection (multi)
        
        self.setWindowTitle("Add Tags" if self.is_add_mode else "Edit Tags")
        self.setMinimumWidth(300)
        self.setMinimumHeight(400)
        
        # Data
        self.all_tags = self.gallery_model.get_all_tags_list()
        self.common_tags = []
        self.tags_state = {} # tag_name -> bool
        
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
                
        # New Tag Input
        input_layout = QHBoxLayout()
        self.new_tag_input = QLineEdit()
        self.new_tag_input.setPlaceholderText("New Tag Name")
        self.new_tag_input.returnPressed.connect(self.add_new_tag)
        input_layout.addWidget(self.new_tag_input)
        
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_new_tag)
        input_layout.addWidget(add_btn)
        
        layout.addLayout(input_layout)
        
        layout.addWidget(QLabel("Select tags to apply:"))
        
        # Tags List
        self.tags_list_widget = QListWidget()
        self.tags_list_widget.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.tags_list_widget)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_data(self):
        if not self.is_add_mode:
            # Single file mode - load existing tags
            details = self.gallery_model.get_image_details(self.target_path)
            if details:
                self.common_tags = details.get("tags", [])
        else:
            self.common_tags = []
            
        # Initialize state
        for tag in self.all_tags:
            self.tags_state[tag] = (tag in self.common_tags)
            
        self.refresh_list()

    def refresh_list(self):
        self.tags_list_widget.clear()
        for tag in self.all_tags:
            item = QListWidgetItem()
            item.setSizeHint(QSize(100, 36))
            self.tags_list_widget.addItem(item)
            
            cb = QCheckBox(tag)
            cb.setChecked(self.tags_state.get(tag, False))
            cb.setStyleSheet("background: transparent; color: #e4e4e7; font-size: 13px; margin: 0px;")
            cb.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            
            self.tags_list_widget.setItemWidget(item, cb)

    def on_item_clicked(self, item):
        cb = self.tags_list_widget.itemWidget(item)
        if cb:
            cb.setChecked(not cb.isChecked())
            self.tags_state[cb.text()] = cb.isChecked()

    def add_new_tag(self):
        name = self.new_tag_input.text().strip()
        if name:
            if self.gallery_model.add_new_tag(name):
                self.all_tags = self.gallery_model.get_all_tags_list()
                self.tags_state[name] = True
                self.refresh_list()
                self.new_tag_input.clear()

    def accept(self):
        # Apply changes
        for tag in self.all_tags:
            is_checked = self.tags_state.get(tag, False)
            
            if not self.is_add_mode:
                # Single File: Add or Remove
                if is_checked:
                    self.gallery_model.add_tag_to_image_path(self.target_path, tag)
                else:
                    self.gallery_model.remove_tag_from_image_path(self.target_path, tag)
            else:
                # Multi-Selection: Only Add (Additive mode as per requirements/existing behavior)
                # "Connect Context Menu for 'Modify Tags' to TagEditDialog."
                # QML: "isMulti ? tagDialog.isAddMode = true"
                # QML logic:
                # if (targetPath !== "") { ... add or remove ... }
                # else { if (isChecked) apply_tag_to_selection(tag) } -> No remove in multi mode
                if is_checked:
                    self.gallery_model.apply_tag_to_selection(tag)
                    
        super().accept()
