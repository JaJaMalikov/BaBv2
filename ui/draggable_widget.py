from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt

class DraggableOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: rgba(0,0,0,120); border-radius: 8px;")
        self._drag_start_position = None

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._drag_start_position = event.globalPosition().toPoint() - self.pos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.RightButton and self._drag_start_position:
            self.move(event.globalPosition().toPoint() - self._drag_start_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self._drag_start_position = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)
