from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import QGraphicsDropShadowEffect
from PySide6.QtGui import QColor

class DraggableOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        # Soft shadow for floating feel
        try:
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(18)
            shadow.setOffset(0, 4)
            shadow.setColor(QColor(0, 0, 0, 150))
            self.setGraphicsEffect(shadow)
        except Exception:
            pass
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


class PanelOverlay(DraggableOverlay):
    """Large panel overlay draggable by left-drag on its border.
    Keeps right-button drag everywhere (from base class).
    """
    def __init__(self, parent=None, border_width: int = 12):
        super().__init__(parent)
        self._border_width = border_width

    def _in_border(self, p: QPoint) -> bool:
        x, y = p.x(), p.y(); w, h = self.width(), self.height(); bw = self._border_width
        return x < bw or y < bw or (w - x) < bw or (h - y) < bw

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._in_border(event.position().toPoint()):
            self._drag_start_position = event.globalPosition().toPoint() - self.pos()
            event.accept(); return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.LeftButton) and self._drag_start_position:
            self.move(event.globalPosition().toPoint() - self._drag_start_position)
            event.accept(); return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._drag_start_position:
            self._drag_start_position = None
            event.accept(); return
        super().mouseReleaseEvent(event)


class DraggableHeader(QWidget):
    """Header bar that drags a target overlay with left mouse button."""
    def __init__(self, target, parent=None):
        super().__init__(parent)
        self._target = target
        self._drag_start = None
        self.setAttribute(Qt.WA_StyledBackground, True)
        # Styling via role property, main stylesheet will handle it
        self.setProperty("role", "overlay-header")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._target is not None:
            self._drag_start = event.globalPosition().toPoint() - self._target.pos()
            event.accept(); return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.LeftButton) and self._drag_start is not None and self._target is not None:
            self._target.move(event.globalPosition().toPoint() - self._drag_start)
            event.accept(); return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._drag_start is not None:
            self._drag_start = None
            event.accept(); return
        super().mouseReleaseEvent(event)
