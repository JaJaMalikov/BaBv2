"""Module providing draggable and resizable overlay widgets."""

import logging
from typing import Optional

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPoint, QRect
from PySide6.QtWidgets import QGraphicsDropShadowEffect
from PySide6.QtGui import QColor


class DraggableOverlay(QWidget):
    """Base overlay that can be moved with the right mouse button."""

    def __init__(self, parent=None) -> None:
        """Initialise the overlay and install a drop shadow effect."""
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        try:
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(18)
            shadow.setOffset(0, 4)
            shadow.setColor(QColor(0, 0, 0, 150))
            self.setGraphicsEffect(shadow)
        except RuntimeError as e:
            logging.debug("Shadow effect unavailable: %s", e)
        self._drag_start_position = None

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        """Begin dragging on right-click or delegate to parent."""
        if event.button() == Qt.RightButton:
            self._drag_start_position = event.globalPosition().toPoint() - self.pos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        """Move the overlay while the right button is held."""
        if event.buttons() & Qt.RightButton and self._drag_start_position:
            self.move(event.globalPosition().toPoint() - self._drag_start_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        """End the drag operation on right button release."""
        if event.button() == Qt.RightButton:
            self._drag_start_position = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class PanelOverlay(DraggableOverlay):
    """Draggable (right-click) panel that can also be resized."""

    def __init__(self, parent=None, border_width: int = 8) -> None:
        """Create a panel overlay with an optional resize border."""
        super().__init__(parent)
        self._border_width = border_width
        self.setMouseTracking(True)

        self._is_resizing = False
        self._resize_edge = None
        self._resize_start_pos = None
        self._resize_start_geom = None

    def _hit_test_corner(self, pos: QPoint) -> Optional[Qt.Corner]:
        """Return resize corner if ``pos`` lies within the border.

        The border thickness is ``self._border_width``; returns ``None`` when the
        cursor is outside this region.
        """
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        bw = self._border_width

        on_left = 0 <= x < bw
        on_right = (w - bw) <= x < w
        on_top = 0 <= y < bw
        on_bottom = (h - bw) <= y < h

        if on_top:
            if on_left:
                return Qt.TopLeftCorner
            if on_right:
                return Qt.TopRightCorner
        elif on_bottom:
            if on_left:
                return Qt.BottomLeftCorner
            if on_right:
                return Qt.BottomRightCorner

        return None

    def _get_edge(self, pos: QPoint) -> Optional[Qt.Corner]:
        """Backward-compatible wrapper around :meth:`_hit_test_corner`."""
        return self._hit_test_corner(pos)

    def leaveEvent(self, event) -> None:  # type: ignore[override]
        """Reset the cursor when it leaves the overlay."""
        self.unsetCursor()  # Fix for sticky cursor
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        """Start resizing on left click or pass to parent."""
        if event.button() == Qt.LeftButton:
            edge = self._get_edge(event.position().toPoint())
            if edge:
                self._is_resizing = True
                self._resize_edge = edge
                self._resize_start_pos = event.globalPosition().toPoint()
                self._resize_start_geom = self.geometry()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        """Stop resizing when the left button is released."""
        if event.button() == Qt.LeftButton and self._is_resizing:
            self._is_resizing = False
            self._resize_edge = None
            self._resize_start_pos = None
            self._resize_start_geom = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        """Resize or update the cursor while the mouse moves."""
        if self._is_resizing and (event.buttons() & Qt.LeftButton):
            delta = event.globalPosition().toPoint() - self._resize_start_pos
            new_geom = QRect(self._resize_start_geom)

            edge = self._resize_edge
            if edge == Qt.TopEdge:
                new_geom.setTop(self._resize_start_geom.top() + delta.y())
            elif edge == Qt.BottomEdge:
                new_geom.setBottom(self._resize_start_geom.bottom() + delta.y())
            elif edge == Qt.LeftEdge:
                new_geom.setLeft(self._resize_start_geom.left() + delta.x())
            elif edge == Qt.RightEdge:
                new_geom.setRight(self._resize_start_geom.right() + delta.x())
            elif edge == Qt.TopLeftCorner:
                new_geom.setTopLeft(self._resize_start_geom.topLeft() + delta)
            elif edge == Qt.TopRightCorner:
                new_geom.setTopRight(self._resize_start_geom.topRight() + delta)
            elif edge == Qt.BottomLeftCorner:
                new_geom.setBottomLeft(self._resize_start_geom.bottomLeft() + delta)
            elif edge == Qt.BottomRightCorner:
                new_geom.setBottomRight(self._resize_start_geom.bottomRight() + delta)

            if new_geom.width() < 200:
                new_geom.setWidth(200)
            if new_geom.height() < 150:
                new_geom.setHeight(150)

            self.setGeometry(new_geom)
            event.accept()
            return

        edge = self._get_edge(event.position().toPoint())
        if not self._is_resizing:
            if edge in [Qt.TopLeftCorner, Qt.BottomRightCorner]:
                self.setCursor(Qt.SizeFDiagCursor)
            elif edge in [Qt.TopRightCorner, Qt.BottomLeftCorner]:
                self.setCursor(Qt.SizeBDiagCursor)
            else:
                self.unsetCursor()

        super().mouseMoveEvent(event)


class DraggableHeader(QWidget):
    """Header bar that drags a target overlay with the left button."""

    def __init__(self, target, parent=None) -> None:
        """Store the target overlay and style the header widget."""
        super().__init__(parent)
        self._target = target
        self._drag_start = None
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setProperty("role", "overlay-header")

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        """Begin dragging the target overlay on left press."""
        if event.button() == Qt.LeftButton and self._target is not None:
            self._drag_start = event.globalPosition().toPoint() - self._target.pos()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        """Move the target overlay while the left button is held."""
        if (
            event.buttons() & Qt.LeftButton
            and self._drag_start is not None
            and self._target is not None
        ):
            self._target.move(event.globalPosition().toPoint() - self._drag_start)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        """End the drag operation when the left button is released."""
        if event.button() == Qt.LeftButton and self._drag_start is not None:
            self._drag_start = None
            event.accept()
            return
        super().mouseReleaseEvent(event)
