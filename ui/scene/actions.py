"""Module for scene-related actions."""

from __future__ import annotations

from typing import TYPE_CHECKING
import logging
from PySide6.QtWidgets import QFileDialog, QInputDialog

from . import scene_io

if TYPE_CHECKING:
    from .scene_controller import MainWindowProtocol


def reset_scene(win: "MainWindowProtocol") -> None:
    """Clear the current scene and create a new blank one."""
    scene_io.create_blank_scene(win, add_default_puppet=False)
    win.scene_controller.set_background_path(None)
    win.ensure_fit()


def set_background(win: "MainWindowProtocol") -> None:
    """Open a file dialog to choose a background image and apply it."""
    file_path: str
    file_path, _ = QFileDialog.getOpenFileName(
        win,
        "Charger une image d'arrière-plan",
        "",
        "Images (*.png *.jpg *.jpeg)",
    )
    if file_path:
        win.scene_controller.set_background_path(file_path)


def set_scene_size(win: "MainWindowProtocol") -> None:
    """Prompt the user for scene width/height and apply to the scene.

    Updates the scene rect, visuals, background fit, and zoom status.
    """
    cur_w, cur_h = win.scene_controller.get_scene_size() if hasattr(win, "scene_controller") else (win.scene_model.scene_width, win.scene_model.scene_height)
    width, ok1 = QInputDialog.getInt(
        win,
        "Taille de la scène",
        "Largeur:",
        cur_w,
        1,
    )
    if not ok1:
        return
    height, ok2 = QInputDialog.getInt(
        win,
        "Taille de la scène",
        "Hauteur:",
        cur_h,
        1,
    )
    if not ok2:
        return

    # Déléguer au SceneController pour centraliser la logique
    try:
        win.scene_controller.set_scene_size(int(width), int(height))
    except (AttributeError, TypeError):
        logging.exception("SceneController set_scene_size failed")
        # Fallback en cas d'indisponibilité (sécurité)
        win.scene_model.scene_width = int(width)
        win.scene_model.scene_height = int(height)
        win.scene.setSceneRect(0, 0, int(width), int(height))
        win._update_scene_visuals()
        win._update_background()
        win._update_zoom_status()
