from PyQt6.QtWidgets import QListView, QMenu, QFileDialog, QProgressDialog, QMessageBox, QWidget
from PyQt6.QtCore import Qt, QSize, QTimer, QPoint
from PyQt6.QtGui import QAction, QCursor, QPainter, QColor
from core.gallery_model import GalleryModel
from core.thumbnail_generator import ThumbnailGenerator
from ui.widgets.tag_edit_dialog import TagEditDialog
from ui.widgets.util.recycle_worker import can_recycle_path, RecycleWorker
from ui.widgets.util.move_worker import MoveWorker
import os

class StickyHeader(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.text = ""
        self.setFixedHeight(50)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
    def set_text(self, text):
        if self.text != text:
            self.text = text
            self.update()
            
    def paintEvent(self, event):
        if not self.text:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        # Solid background matching the gallery background (#0f0f13)
        painter.fillRect(self.rect(), QColor("#0f0f13"))
        
        # Left indicator bar (matching our styled delegates)
        # painter.fillRect(10, 15, 4, 20, QColor("#0078d4")) # Since we decided not to do left accent bar on headers in gallery view, we don't draw it here to stay consistent with month headers.
        
        # Pen color and font
        painter.setPen(QColor("#e4e4e7"))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(14)
        painter.setFont(font)
        
        # Position text slightly offset
        text_rect = self.rect().adjusted(10, 10, -10, -10)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.text)

class GalleryListView(QListView):
    THUMB_SIZE = 128
    SPACING = 10
    COL_WIDTH = THUMB_SIZE + SPACING

    def __init__(self, parent=None):
        super().__init__(parent)
        self.gallery_model = GalleryModel.instance()
        self.thumbnail_generator = ThumbnailGenerator.instance()
        
        # Initialize Sticky Header
        self.sticky_header = StickyHeader(self.viewport())
        self.sticky_header.hide()
        
        self.setMouseTracking(True)
        self.setSelectionMode(QListView.SelectionMode.NoSelection) # We handle custom selection
        self.setFrameShape(QListView.Shape.NoFrame)
        self.setStyleSheet("QListView { background-color: transparent; }")
        
        # Disable default vertical scrolling scrollbars (we let listview handle its own scrollbar, but we style it if needed)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Set layout mode
        self.setResizeMode(QListView.ResizeMode.Adjust)

        # Scroll debounce for thumbnail queue optimization
        self.scroll_timer = QTimer(self)
        self.scroll_timer.setSingleShot(True)
        self.scroll_timer.timeout.connect(self.on_scroll_timeout)
        self.verticalScrollBar().valueChanged.connect(self.on_scroll)

    def setModel(self, model):
        super().setModel(model)
        if model:
            model.layoutChanged.connect(self.update_sticky_header)
            model.modelReset.connect(self.update_sticky_header)
            model.rowsInserted.connect(self.update_sticky_header)
            model.rowsRemoved.connect(self.update_sticky_header)
        self.update_sticky_header()

    def on_scroll(self):
        # Cancel any pending requests while active scrolling is happening
        self.thumbnail_generator.clearQueue()
        self.scroll_timer.start(80) # 80ms debounce
        self.update_sticky_header()

    def on_scroll_timeout(self):
        # Clear out "not found" flags from delegate cache to allow re-requesting only for visible ones
        delegate = self.itemDelegate()
        if delegate and hasattr(delegate, "thumb_cache"):
            delegate.thumb_cache.clear_failures()
        self.viewport().update()

    def update_max_queue_size(self):
        width = self.viewport().width()
        height = self.viewport().height()
        cols = max(1, (width - self.SPACING) // self.COL_WIDTH)
        rows = (height // self.COL_WIDTH) + 2
        self.thumbnail_generator.setMaxQueueSize(cols * rows)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Recalculate columns based on viewport width
        width = self.viewport().width()
        cols = max(1, (width - self.SPACING) // self.COL_WIDTH)
        self.gallery_model.set_columns(cols)
        self.update_max_queue_size()
        self.update_sticky_header()

    def _get_image_at_pos(self, pos):
        index = self.indexAt(pos)
        if not index.isValid():
            return None, None
            
        item = index.data(Qt.ItemDataRole.UserRole)
        if not item or item.get("type") != "images":
            return None, None
            
        # Determine which column was clicked
        click_x = pos.x()
        col = click_x // self.COL_WIDTH
        images = item.get("images", [])
        if 0 <= col < len(images):
            return images[col]["path"], images[col]["thumbnailPath"]
            
        return None, None

    def mousePressEvent(self, event):
        path, _ = self._get_image_at_pos(event.pos())
        if path:
            if event.button() == Qt.MouseButton.LeftButton:
                modifiers = int(event.modifiers().value)
                self.gallery_model.handle_selection(path, modifiers)
                return
            elif event.button() == Qt.MouseButton.RightButton:
                # If not selected, select it exclusively first
                if not self.gallery_model.is_selected(path):
                    self.gallery_model.handle_selection(path, 0)
                # Show context menu
                self.show_context_menu(path, event.globalPosition().toPoint())
                return
                
        # If clicked elsewhere, clear selection
        if event.button() == Qt.MouseButton.LeftButton:
            self.gallery_model.clear_selection()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        path, _ = self._get_image_at_pos(event.pos())
        if path and event.button() == Qt.MouseButton.LeftButton:
            self.gallery_model.openImageRequested.emit(path)
            return
        super().mouseDoubleClickEvent(event)

    def show_context_menu(self, image_path, global_pos):
        menu = QMenu(self)
        selected = self.gallery_model.get_selected_paths()
        
        if len(selected) <= 1:
            open_action = QAction("Open", self)
            open_action.triggered.connect(lambda: self.gallery_model.openImageRequested.emit(image_path))
            menu.addAction(open_action)
        
            reveal_action = QAction("Reveal in File Explorer", self)
            reveal_action.triggered.connect(lambda: self.gallery_model.reveal_file(image_path))
            menu.addAction(reveal_action)
        
        # Add Tag / Edit Tags
        if len(selected) <= 1:
            edit_tags_action = QAction("Edit Tags", self)
            target = image_path
        else:
            edit_tags_action = QAction("Add Tags", self)
            target = ""
        
        edit_tags_action.triggered.connect(lambda: self.open_tag_dialog(target))
        menu.addAction(edit_tags_action)

        # Remove from current tag filter
        active_filters = self.gallery_model.active_filters
        if len(active_filters) == 1 and active_filters[0].get('type') == 'tag' and not active_filters[0].get('negated', False):
            tag_name = active_filters[0].get('value')
            remove_action = QAction(f"Remove from {tag_name}", self)
            remove_action.triggered.connect(lambda: self.gallery_model.remove_tag_from_selection(tag_name))
            menu.addAction(remove_action)
            
        move_action = QAction("Move to...", self)
        move_action.triggered.connect(self.trigger_move)
        menu.addAction(move_action)
        
        recycle_action = QAction("Move to Recycle Bin", self)
        recycle_action.triggered.connect(self.trigger_recycle)
        menu.addAction(recycle_action)
        
        menu.exec(global_pos)

    def open_tag_dialog(self, target):
        dialog = TagEditDialog(target_path=target, parent=self)
        dialog.exec()

    def trigger_recycle(self):
        selected = self.gallery_model.get_selected_paths()
        if not selected:
            return
            
        permanent_mode = False
        if any(not can_recycle_path(path) for path in selected):
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Warning")
            msg_box.setText("The selected items cannot be recycled. Proceeding with this action will permanently delete them. Proceed anyway?")
            proceed_button = msg_box.addButton("Proceed Anyway", QMessageBox.ButtonRole.AcceptRole)
            cancel_button = msg_box.addButton(QMessageBox.StandardButton.Cancel)
            msg_box.setDefaultButton(cancel_button)
            msg_box.exec()
            
            if msg_box.clickedButton() == cancel_button:
                return
            permanent_mode = True

        confirm_box = QMessageBox(self)
        confirm_box.setWindowTitle("Confirm Action")
        if permanent_mode:
            confirm_box.setText(f"Permanently delete {len(selected)} items?")
        else:
            confirm_box.setText(f"Recycle {len(selected)} items?")
            
        yes_button = confirm_box.addButton(QMessageBox.StandardButton.Yes)
        cancel_button = confirm_box.addButton(QMessageBox.StandardButton.Cancel)
        confirm_box.setDefaultButton(cancel_button)
        confirm_box.exec()
        
        if confirm_box.clickedButton() == cancel_button:
            return

        self.progress_dialog = QProgressDialog("Deleting files...", None, 0, len(selected), self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.show()

        self.worker = RecycleWorker(selected, permanent_mode)
        self.worker.progress.connect(self.progress_dialog.setValue)
        self.worker.fileRemoved.connect(self.gallery_model.handle_file_removed)
        self.worker.finished.connect(lambda succeeded: self.on_recycle_finished(succeeded, permanent_mode))
        self.worker.error.connect(lambda err_msg, succeeded, total: self.on_recycle_error(err_msg, succeeded, total, permanent_mode))
        self.worker.start()

    def on_recycle_finished(self, succeeded, permanent_mode):
        self.progress_dialog.close()
        action_text = "deleted" if permanent_mode else "recycled"
        QMessageBox.information(self, "Success", f"{succeeded} items successfully {action_text}")
        self.gallery_model.clear_selection()
        self.gallery_model.refresh()

    def on_recycle_error(self, err_msg, succeeded, total, permanent_mode):
        self.progress_dialog.close()
        action_text = "permanently deleted" if permanent_mode else "recycled"
        QMessageBox.warning(self, "Error", f"An error occured. {succeeded}/{total} items were {action_text}")
        self.gallery_model.clear_selection()
        self.gallery_model.refresh()

    def trigger_move(self):
        selected = self.gallery_model.get_selected_paths()
        if not selected:
            return
            
        dest_dir = QFileDialog.getExistingDirectory(self, "Select Destination Directory")
        if not dest_dir:
            return
            
        self.progress_dialog = QProgressDialog("Moving files...", "Cancel", 0, len(selected), self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.show()
        
        self.worker = MoveWorker(selected, dest_dir)
        self.worker.progress.connect(self.progress_dialog.setValue)
        self.worker.fileMoved.connect(self.gallery_model.handle_file_moved)
        self.worker.finished.connect(self.on_move_finished)
        self.worker.start()

    def on_move_finished(self):
        self.progress_dialog.close()
        self.gallery_model.clear_selection()
        self.gallery_model.refresh()

    def get_active_header(self):
        # Find index at top left of viewport
        top_left_index = self.indexAt(QPoint(10, 5))
        if not top_left_index.isValid():
            return None, None
            
        row = top_left_index.row()
        # Go backwards to find the nearest header
        for r in range(row, -1, -1):
            idx = self.model().index(r, 0)
            item = idx.data(Qt.ItemDataRole.UserRole)
            if item and item.get("type") == "header":
                return item.get("month_text", ""), r
                
        return None, None

    def update_sticky_header(self):
        if not self.model() or self.model().rowCount() == 0:
            self.sticky_header.hide()
            return
            
        month_text, active_row = self.get_active_header()
        if not month_text:
            self.sticky_header.hide()
            return
            
        # Find next header to compute push offset
        next_header_row = -1
        for r in range(active_row + 1, self.model().rowCount()):
            idx = self.model().index(r, 0)
            item = idx.data(Qt.ItemDataRole.UserRole)
            if item and item.get("type") == "header":
                next_header_row = r
                break
                
        offset_y = 0
        H = 50 # Header height
        if next_header_row != -1:
            next_idx = self.model().index(next_header_row, 0)
            rect = self.visualRect(next_idx)
            if rect.y() < H:
                offset_y = rect.y() - H
                
        self.sticky_header.set_text(month_text)
        self.sticky_header.setGeometry(0, offset_y, self.viewport().width(), H)
        self.sticky_header.show()
        self.sticky_header.raise_()
