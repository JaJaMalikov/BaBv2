"""Module for managing scene visuals, such as borders and background."""

from __future__ import annotations

import logging
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QGraphicsPixmapItem
from PySide6.QtGui import QPen, QColor, QPixmap
from PySide6.QtCore import Qt


class SceneVisuals:
    """Decorates the scene with border/size label and manages background image."""

    def __init__(self, win) -> None:
        """Store reference to the main window and initialize placeholders."""
        self.win = win
        self.scene_border_item: QGraphicsRectItem | None = None
        self.scene_size_text_item: QGraphicsTextItem | None = None
        self.background_item: QGraphicsPixmapItem | None = None

    def setup(self) -> None:
        """Create visual helpers and attach them to the scene."""
        self.scene_border_item = QGraphicsRectItem()
        self.scene_size_text_item = QGraphicsTextItem()
        self.win.scene.addItem(self.scene_border_item)
        self.win.scene.addItem(self.scene_size_text_item)
        self.update_scene_visuals()

    def update_scene_visuals(self) -> None:
        """Update border rectangle and size label from model values."""
        if not self.scene_border_item or not self.scene_size_text_item:
            return
        rect = self.win.scene.sceneRect()
        self.scene_border_item.setPen(QPen(QColor(100, 100, 100), 2, Qt.DashLine))
        self.scene_border_item.setRect(rect)
        text = f"{self.win.scene_model.scene_width}x{self.win.scene_model.scene_height}"
        self.scene_size_text_item.setPlainText(text)
        self.scene_size_text_item.setDefaultTextColor(QColor(150, 150, 150))
        text_rect = self.scene_size_text_item.boundingRect()
        self.scene_size_text_item.setPos(
            rect.right() - text_rect.width() - 10,
            rect.bottom() - text_rect.height() - 10,
        )

    def update_background(self) -> None:
        """Load and display the background image if one is configured."""
        # Remove previous
        if self.background_item:
            self.win.scene.removeItem(self.background_item)
            self.background_item = None

        if not self.win.scene_model.background_path:
            return
        try:
            pixmap = QPixmap(self.win.scene_model.background_path)
            if pixmap.isNull():
                raise FileNotFoundError(
                    f"Could not load image: {self.win.scene_model.background_path}"
                )
            # Route model size changes via the controller/service to respect boundaries.
            # Avoid recursion by returning early: the resize signal will trigger
            # update_background() again where sizes already match, and we will proceed.
            if (
                int(getattr(self.win.scene_model, "scene_width", 0)) != pixmap.width()
                or int(getattr(self.win.scene_model, "scene_height", 0))
                != pixmap.height()
            ):
                try:
                    self.win.scene_controller.set_scene_size(pixmap.width(), pixmap.height())
                    return
                except (AttributeError, RuntimeError):
                    # As an ultimate fallback, keep UI responsive without mutating the model.
                    self.win.scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())
                    self.update_scene_visuals()
            # Create and add the background item when sizes are in sync
            self.background_item = QGraphicsPixmapItem(pixmap)
            self.background_item.setZValue(-10000)
            self.win.scene.addItem(self.background_item)
            self.win.ensure_fit()
        except FileNotFoundError as e:
            logging.error("Failed to load background image: %s", e)
        except (OSError, RuntimeError, ValueError):
            logging.exception("Unexpected error while updating background")
