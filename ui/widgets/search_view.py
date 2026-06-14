from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QScrollArea, QFrame, QGridLayout, QInputDialog, QMessageBox,
    QDateEdit, QDialog, QDialogButtonBox, QListWidget, QAbstractItemView,
    QCalendarWidget
)
from PyQt6.QtCore import Qt, QSize, QDate
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from ui.widgets.util.flow_layout import FlowLayout
import json
from core.gallery_model import GalleryModel

def create_colored_pixmap(icon_path, color):
    pm = QIcon(icon_path).pixmap(24, 24)
    if pm.isNull():
        return pm
    colored = QPixmap(pm.size())
    colored.fill(Qt.GlobalColor.transparent)
    painter = QPainter(colored)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
    painter.drawPixmap(0, 0, pm)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(colored.rect(), color) 
    painter.end()
    return colored

class FilterChip(QFrame):
    def __init__(self, text, on_close, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self.setStyleSheet("""
            FilterChip {
                background-color: #e0e0e0;
                border-radius: 15px;
                border: 1px solid #c0c0c0;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 0, 5, 0)
        layout.setSpacing(5)
        self.setLayout(layout)
        
        label = QLabel(text)
        label.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(label)
        
        close_btn = QPushButton()
        close_btn.setFixedSize(20, 20)
        close_btn.setIcon(QIcon(create_colored_pixmap("assets/icons/x.svg", Qt.GlobalColor.black)))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setFlat(True)
        close_btn.setStyleSheet(f"""
            QPushButton {{ border: none; font-weight: bold; }}
            QPushButton:hover {{ color: red; }}
        """)
        close_btn.clicked.connect(on_close)
        layout.addWidget(close_btn)

class SearchView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gallery_model = GalleryModel.instance()
        self.active_filters = [] # List of dicts: {type, value, negated, label}
        self.is_negated_mode = False
        
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # 1. Search Bar Area
        search_bar_frame = QFrame()
        search_bar_frame.setMinimumHeight(60)
        search_bar_layout = QHBoxLayout(search_bar_frame)
        search_bar_layout.setContentsMargins(10, 10, 10, 10)
        
        # Input Area (Chips)
        self.chips_container = QWidget()
        self.chips_container.setObjectName("chips_container")
        self.chips_container.setStyleSheet("""
            #chips_container {
                background-color: white;
                border: 1px solid #c0c0c0;
                border-radius: 4px;
            }
        """)
        
        self.container_layout = QHBoxLayout(self.chips_container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.placeholder_label = QLabel("Start by adding a filter...")
        self.placeholder_label.setStyleSheet("font-style: italic;")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.container_layout.addWidget(self.placeholder_label)
        
        self.chips_flow_widget = QWidget()
        self.chips_layout = FlowLayout(self.chips_flow_widget)
        self.chips_layout.setContentsMargins(5, 5, 5, 5)
        self.chips_layout.setSpacing(5)
        self.container_layout.addWidget(self.chips_flow_widget)
        
        search_bar_layout.addWidget(self.chips_container, 1)
        
        # Search Button
        self.search_btn = QPushButton()
        self.search_btn.setIcon(QIcon("assets/icons/search.svg"))

        self.search_btn.setIconSize(QSize(24, 24))
        self.search_btn.setFixedSize(50, 40)
        self.search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #0078D7;
                color: white;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: #0063B1;
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
            }}
        """)
        self.search_btn.clicked.connect(self.perform_search)
        self.search_btn.setEnabled(False)
        search_bar_layout.addWidget(self.search_btn)
        
        main_layout.addWidget(search_bar_frame)
        
        # 2. Filter Controls (Scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        scroll.setWidget(scroll_content)
        
        content_layout = QVBoxLayout(scroll_content)
        
        # Heading & Negation Toggle
        header_layout = QHBoxLayout()
        header = QLabel("Filters")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        self.negate_btn = QPushButton("Toggle negative filters")
        self.negate_btn.setCheckable(True)
        self.negate_btn.clicked.connect(self.toggle_negation)
        self.negate_btn.setStyleSheet(f"""
            QPushButton:checked {{ background-color: red; color: white; border: 1px solid red; }}
            QPushButton {{ 
                padding: 5px 10px;
                border-radius: 4px;
            }}
        """)
        header_layout.addWidget(self.negate_btn)
        content_layout.addLayout(header_layout)
        
        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        content_layout.addWidget(line)
        
        # Filter Buttons Grid
        grid = QGridLayout()

        
        # Dates
        grid.addWidget(self.create_icon_label("assets/icons/calendar.svg"), 0, 0, Qt.AlignmentFlag.AlignTop)
        date_flow = QWidget()
        date_flow_layout = FlowLayout(date_flow)
        date_flow_layout.addWidget(self.create_filter_btn("Before date", self.open_date_before))
        date_flow_layout.addWidget(self.create_filter_btn("Since date", self.open_date_since))
        date_flow_layout.addWidget(self.create_filter_btn("Between dates", self.open_date_between))
        grid.addWidget(date_flow, 0, 1)

        # Camera
        grid.addWidget(self.create_icon_label("assets/icons/camera.svg"), 1, 0, Qt.AlignmentFlag.AlignTop)
        cam_flow = QWidget()
        cam_flow_layout = FlowLayout(cam_flow)
        cam_flow_layout.addWidget(self.create_filter_btn("Taken with camera", self.open_camera_dialog))
        cam_flow_layout.addWidget(self.create_filter_btn("Taken with lens", self.open_lens_dialog))
        grid.addWidget(cam_flow, 1, 1)
        
        # Folder/File
        grid.addWidget(self.create_icon_label("assets/icons/folder.svg"), 2, 0, Qt.AlignmentFlag.AlignTop)
        file_flow = QWidget()
        file_flow_layout = FlowLayout(file_flow)
        file_flow_layout.addWidget(self.create_filter_btn("In folder", self.open_folder_dialog))
        file_flow_layout.addWidget(self.create_filter_btn("Has file extension", self.open_extension_dialog))
        file_flow_layout.addWidget(self.create_filter_btn("Filename starts with", self.open_filename_dialog))
        grid.addWidget(file_flow, 2, 1)

        # Tags
        grid.addWidget(self.create_icon_label("assets/icons/tag.svg"), 3, 0, Qt.AlignmentFlag.AlignTop)
        tag_flow = QWidget()
        tag_flow_layout = FlowLayout(tag_flow)
        tag_flow_layout.addWidget(self.create_filter_btn("Has tag", self.open_tag_dialog))
        grid.addWidget(tag_flow, 3, 1)
        
        content_layout.addLayout(grid)
        content_layout.addStretch()
        
        main_layout.addWidget(scroll)
        
        self.update_chips_display()

    def create_icon_label(self, icon_path):
        lbl = QLabel()
        pm = create_colored_pixmap(icon_path, Qt.GlobalColor.black)
        lbl.setPixmap(pm)
        lbl.setFixedSize(30, 30)
        return lbl

    def create_filter_btn(self, text, slot):
        btn = QPushButton(text)
        btn.clicked.connect(slot)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                padding: 6px 12px;
                text-align: left;
                border-radius: 6px;
                color: #333333;
            }}
            QPushButton:hover {{
                background-color: #e0e0e0;
                border-color: #b0b0b0;
            }}
        """)
        return btn

    def toggle_negation(self):
        self.is_negated_mode = self.negate_btn.isChecked()

    def add_filter(self, type_, value, label=None):
        if label is None:
            # Generate label similar to QML logic
            if type_ == "tag": label = f"Tag: {value}"
            elif type_ == "before": label = f"Before {value}"
            elif type_ == "since": label = f"Since {value}"
            elif type_ == "camera": label = f"Camera: \"{value}\""
            elif type_ == "lens": label = f"Lens: \"{value}\""
            elif type_ == "folder": label = f"In folder: \"{value}\""
            elif type_ == "extension": label = f"Extension: {value.upper()}"
            elif type_ == "filename": label = f"Filename: starts with \"{value}\""
            elif type_ == "date_between":
                 data = json.loads(value)
                 label = f"Between {data['start']} and {data['end']}"
            else: label = f"{type_}: {value}"
            
        display_label = ("NOT " if self.is_negated_mode else "") + label
        
        self.active_filters.append({
            "type": type_,
            "value": value,
            "negated": self.is_negated_mode,
            "label": display_label
        })
        self.update_chips_display()

    def remove_filter(self, index):
        if 0 <= index < len(self.active_filters):
            self.active_filters.pop(index)
            self.update_chips_display()

    def update_chips_display(self):
        # Clear existing chips
        while self.chips_layout.count():
            item = self.chips_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.active_filters:
            self.placeholder_label.show()
            self.chips_flow_widget.hide()
            self.search_btn.setEnabled(False)
        else:
            self.placeholder_label.hide()
            self.chips_flow_widget.show()
            for i, f in enumerate(self.active_filters):
                chip = FilterChip(f["label"], lambda checked=False, idx=i: self.remove_filter(idx))
                self.chips_layout.addWidget(chip)
            self.search_btn.setEnabled(True)

    def perform_search(self):
        # Prepare filters for backend
        filters_for_backend = []
        for f in self.active_filters:
            filters_for_backend.append({
                "type": f["type"],
                "value": f["value"],
                "negated": f["negated"]
            })
        
        self.gallery_model.search(filters_for_backend)
        
        # Navigate to Gallery tab
        self.gallery_model.request_switch_to_gallery()

    # --- Dialog Implementations ---
    
    def open_text_dialog(self, title, label, filter_type):
        text, ok = QInputDialog.getText(self, title, label)
        if ok and text:
            self.add_filter(filter_type, text)

    def open_filename_dialog(self):
        self.open_text_dialog("Filename Filter", "Filename starts with:", "filename")

    def open_extension_dialog(self):
        self.open_text_dialog("Extension Filter", "File extension (e.g. jpg):", "extension")

    def open_folder_dialog(self):
        folder, ok = QInputDialog.getText(self, "Folder Filter", "Folder path contains:")
        if ok and folder:
             self.add_filter("folder", folder)

    def open_camera_dialog(self):
        cameras = self.gallery_model.get_all_cameras()
        if not cameras:
            QMessageBox.information(self, "No Cameras", "No cameras found in database.")
            return
        item, ok = QInputDialog.getItem(self, "Camera Filter", "Select Camera:", cameras, 0, False)
        if ok and item:
            self.add_filter("camera", item)

    def open_lens_dialog(self):
        lenses = self.gallery_model.get_all_lenses()
        if not lenses:
            QMessageBox.information(self, "No Lenses", "No lenses found in database.")
            return
        item, ok = QInputDialog.getItem(self, "Lens Filter", "Select Lens:", lenses, 0, False)
        if ok and item:
            self.add_filter("lens", item)

    def open_tag_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Tag")
        dialog.setMinimumWidth(300)
        layout = QVBoxLayout(dialog)
        
        list_widget = QListWidget()
        tags = self.gallery_model.get_all_tags_list()
        list_widget.addItems(tags)
        layout.addWidget(list_widget)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_items = list_widget.selectedItems()
            if selected_items:
                self.add_filter("tag", selected_items[0].text())

    def open_date_before(self):
        self._open_date_picker("before", "Before Date")

    def open_date_since(self):
        self._open_date_picker("since", "Since Date")

    def _open_date_picker(self, type_, title):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout(dialog)
        
        cal = QDateEdit()
        cal.setCalendarPopup(True)
        cal.setDate(QDate.currentDate())
        layout.addWidget(cal)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            date_str = cal.date().toString("yyyy-MM-dd")
            self.add_filter(type_, date_str)

    def open_date_between(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Date Range")
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel("Start Date:"))
        start_cal = QDateEdit()
        start_cal.setCalendarPopup(True)
        start_cal.setDate(QDate.currentDate().addDays(-7))
        layout.addWidget(start_cal)
        
        layout.addWidget(QLabel("End Date:"))
        end_cal = QDateEdit()
        end_cal.setCalendarPopup(True)
        end_cal.setDate(QDate.currentDate())
        layout.addWidget(end_cal)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            start_str = start_cal.date().toString("yyyy-MM-dd")
            end_str = end_cal.date().toString("yyyy-MM-dd")
            val = json.dumps({"start": start_str, "end": end_str})
            self.add_filter("date_between", val, label=None)
