# Copyright (C) 2013 Riverbank Computing Limited.
# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

from PyQt6.QtCore import Qt, QMargins, QPoint, QRect, QSize
from PyQt6.QtWidgets import QLayout, QSizePolicy

class FlowLayout(QLayout):
    def __init__(self, parent=None):
        super().__init__(parent)

        if parent is not None:
            self.setContentsMargins(QMargins(0, 0, 0, 0))

        self._item_list = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]

        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)

        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._do_layout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()

        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())

        margins = self.contentsMargins()
        margin_top = margins.top()
        size += QSize(2 * margin_top, 2 * margin_top)
        return size

    def _do_layout(self, rect, test_only):
        margins = self.contentsMargins()
        left = margins.left()
        top = margins.top()
        right = margins.right()
        bottom = margins.bottom()

        effective_rect = rect.adjusted(left, top, -right, -bottom)
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0
        spacing = self.spacing()

        # Retrieve the style to calculate layout spacing outside of the loop
        style = None
        parent_widget = self.parentWidget()
        if parent_widget:
            style = parent_widget.style()
        if not style:
            for item in self._item_list:
                widget = item.widget()
                if widget:
                    style = widget.style()
                    break
        if not style:
            from PyQt6.QtWidgets import QApplication
            style = QApplication.style()

        if style:
            layout_spacing_x = style.layoutSpacing(
                QSizePolicy.ControlType.PushButton, QSizePolicy.ControlType.PushButton,
                Qt.Orientation.Horizontal
            )
            layout_spacing_y = style.layoutSpacing(
                QSizePolicy.ControlType.PushButton, QSizePolicy.ControlType.PushButton,
                Qt.Orientation.Vertical
            )
        else:
            layout_spacing_x = 0
            layout_spacing_y = 0

        space_x = spacing + layout_spacing_x
        space_y = spacing + layout_spacing_y
        effective_right = effective_rect.right()

        for item in self._item_list:
            widget = item.widget()
            if not widget:
                continue

            size_hint = item.sizeHint()
            w = size_hint.width()
            h = size_hint.height()
            
            next_x = x + w + space_x
            if next_x - space_x > effective_right and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + space_y
                next_x = x + w + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), size_hint))

            x = next_x
            line_height = max(line_height, h)

        return y + line_height - rect.y() + bottom