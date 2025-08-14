"""Module providing QGraphicsItem subclasses for scene objects.

This module defines `ObjectPixmapItem` and `ObjectSvgItem` for representing
image and SVG objects in the scene, with a mixin for common functionality.
"""

import logging
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsItem
from PySide6.QtSvgWidgets import QGraphicsSvgItem


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
        """Handles item changes and updates the scene model accordingly."""
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
                    obj = mw.scene_model.objects.get(name)
                    if obj:
                        obj.x = self.x()
                        obj.y = self.y()
                        obj.rotation = self.rotation()
                        obj.scale = self.scale()
                        obj.z = int(self.zValue())
                        # If a keyframe exists at current frame, persist state in it
                        kf = mw.scene_model.keyframes.get(mw.scene_model.current_frame)
                        if kf is not None:
                            kf.objects[name] = obj.to_dict()
                    # Sync selection with inspector
                    if change == QGraphicsItem.ItemSelectedHasChanged and bool(value):
                        mw.select_object_in_inspector(name)
            except Exception as e:
                logging.error(f"Error in itemChange for {name}: {e}")
        return super().itemChange(change, value)


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
