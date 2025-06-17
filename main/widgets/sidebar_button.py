from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt

class SidebarButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._selected = False
        self._hovered = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 12px;
                padding: 0px;
            }
            QPushButton:hover {
                background: #29292b;
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

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        marker_width = 4
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
        painter.drawRoundedRect(0, marker_y, marker_width, marker_height, 2, 2)
