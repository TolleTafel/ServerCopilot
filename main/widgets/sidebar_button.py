from PyQt6.QtWidgets import QPushButton, QWidget, QHBoxLayout
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt

class SidebarButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._selected = False
        self._hovered = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setContentsMargins(3, 3, 3, 3)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 12px;
                padding-left: 0px;
                padding-right: 0px;
                padding-top: 0px;
                padding-bottom: 0px;
            }
            QPushButton:hover {
                background-color: #29292b;
            }
        """)

    def setSelected(self, selected: bool):
        self._selected = selected
        self.update()

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    # Remove marker drawing from here
    def paintEvent(self, event):
        super().paintEvent(event)

class SidebarButtonWithMarker(QWidget):
    def __init__(self, button: SidebarButton):
        super().__init__()
        self.button = button
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addSpacing(10)  # Space for marker
        layout.addWidget(self.button)
        self._selected = False
        self._hovered = False
        self.button.enterEvent = self.enterEvent
        self.button.leaveEvent = self.leaveEvent

    def setSelected(self, selected: bool):
        self._selected = selected
        self.button.setSelected(selected)
        self.update()

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        return super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        return super().leaveEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        marker_width = 3
        marker_x = 2
        if self._selected:
            marker_height = int(self.height() * 0.7)
            marker_y = (self.height() - marker_height) // 2
            color = QColor("#ffffff")
            opacity = 1.0
        elif self._hovered:
            marker_height = int(self.height() * 0.35)
            marker_y = (self.height() - marker_height) // 2
            color = QColor("#ffffff")
            opacity = 0.5
        else:
            return
        painter.setPen(Qt.PenStyle.NoPen)
        color.setAlphaF(opacity)
        painter.setBrush(color)
        painter.drawRoundedRect(marker_x, marker_y, marker_width, marker_height, 2, 2)
