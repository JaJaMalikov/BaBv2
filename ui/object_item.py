"""Module providing QGraphicsItem subclasses for scene objects.

This module defines `ObjectPixmapItem` and `ObjectSvgItem` for representing
image and SVG objects in the scene, with a mixin for common functionality.
"""

import logging
import math
from typing import Optional

from PySide6.QtGui import QPixmap, QPolygonF, QColor, QBrush, QPen, QPainter
from PySide6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsItem,
    QGraphicsPolygonItem,
    QStyleOptionGraphicsItem,
    QWidget,
)
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtCore import QPointF, Qt


class _ObjectItemMixin:
    """A mixin for object items, providing context and item change handling."""

    def set_context(self, main_window, obj_name):
        """Sets the context for the object item.

        Args:
            main_window: The main window of the application.
            obj_name: The name of the object.
        """
        self._mw = main_window
        self._obj_name = obj_name
        # Activer la sélection (stroke par défaut)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    def itemChange(self, change, value):
        """Handles item changes and updates the scene model accordingly.

        Defensive: avoid raising from Qt callbacks which can destabilize the app
        (observed OverflowError in tests). Keep side effects minimal and route
        user-driven changes through controllers elsewhere.
        """
        mw = getattr(self, "_mw", None)
        if mw and getattr(mw, "_suspend_item_updates", False):
            return super().itemChange(change, value)
        if change in (
            QGraphicsItem.ItemPositionHasChanged,
            QGraphicsItem.ItemRotationHasChanged,
            QGraphicsItem.ItemScaleHasChanged,
            QGraphicsItem.ItemSelectedHasChanged,
        ):
            name = getattr(self, "_obj_name", None)
            try:
                if mw and name:
                    # Light-touch: update cached transform for immediate feedback.
                    # Persistent model updates are handled by controllers.
                    obj = mw.scene_model.objects.get(name)
                    if obj:
                        try:
                            obj.x = float(self.x())
                            obj.y = float(self.y())
                            obj.rotation = float(self.rotation())
                            obj.scale = float(self.scale())
                            obj.z = int(self.zValue())
                        except Exception:
                            # Never propagate exceptions from here
                            logging.debug("Non-fatal: failed to mirror item transform to model for %s", name)
                    # Sync selection with inspector when becoming selected
                    if change == QGraphicsItem.ItemSelectedHasChanged:
                        selected_flag = False
                        try:
                            selected_flag = bool(value)
                        except Exception:
                            try:
                                selected_flag = int(value) != 0  # type: ignore[arg-type]
                            except Exception:
                                selected_flag = False
                        if selected_flag:
                            try:
                                # Some legacy controllers expose this helper; guard existence
                                ctrl = getattr(mw, "controller", None)
                                if ctrl and hasattr(ctrl, "select_object_in_inspector"):
                                    ctrl.select_object_in_inspector(name)
                            except Exception:
                                # Best-effort only
                                logging.debug("Selection sync failed for %s", name)
            except Exception as e:
                logging.debug("itemChange swallowed exception for %s: %s", name, e)
        try:
            return super().itemChange(change, value)
        except Exception:
            logging.debug("super().itemChange failed; returning original value")
            return value


class ObjectPixmapItem(_ObjectItemMixin, QGraphicsPixmapItem):
    """A QGraphicsPixmapItem for scene objects."""

    def __init__(self, file_path: str):
        """Initializes the pixmap item.

        Args:
            file_path: The path to the image file.
        """
        super().__init__(QPixmap(file_path))


class ObjectSvgItem(_ObjectItemMixin, QGraphicsSvgItem):
    """A QGraphicsSvgItem for scene objects."""

    def __init__(self, file_path: str):
        """Initializes the SVG item.

        Args:
            file_path: The path to the SVG file.
        """
        super().__init__(file_path)


# Default light properties
DEFAULT_LIGHT_COLOR = "#FFFFE0"
DEFAULT_LIGHT_CONE_ANGLE = 45.0
DEFAULT_LIGHT_CONE_REACH = 500.0


class LightItem(QGraphicsPolygonItem, _ObjectItemMixin):
    """A QGraphicsPolygonItem that simulates a light source by setting the painter's composition mode."""

    def __init__(
        self,
        color_str: str = DEFAULT_LIGHT_COLOR,
        angle: float = DEFAULT_LIGHT_CONE_ANGLE,
        reach: float = DEFAULT_LIGHT_CONE_REACH,
    ):
        QGraphicsPolygonItem.__init__(self)

        self.color = QColor(color_str)
        self.color.setAlpha(60)
        self.angle = angle
        self.reach = reach

        self.setPen(QPen(Qt.NoPen))
        self.setBrush(QBrush(self.color))

        self._update_polygon()

    def _update_polygon(self):
        """Updates the polygon shape based on angle and reach."""
        polygon = QPolygonF()
        polygon.append(QPointF(0, 0))  # Apex

        half_angle_rad = (self.angle / 2.0) * (math.pi / 180.0)

        p_left = QPointF(-self.reach * math.tan(half_angle_rad), self.reach)
        p_right = QPointF(self.reach * math.tan(half_angle_rad), self.reach)

        polygon.append(p_left)
        polygon.append(p_right)

        self.setPolygon(polygon)

    def set_light_properties(self, color: QColor, angle: float, reach: float):
        """Update the light's visual properties."""
        self.color = color
        self.angle = angle
        self.reach = reach
        self.setBrush(QBrush(self.color))
        self._update_polygon()

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: Optional[QWidget] = None,
    ) -> None:
        """Paint the item with a screen composition mode to simulate light."""
        painter.setCompositionMode(QPainter.CompositionMode_Screen)
        super().paint(painter, option, widget)
