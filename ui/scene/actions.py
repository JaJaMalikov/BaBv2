"""Module for scene-related actions."""

from __future__ import annotations

from typing import Any
import logging
from PySide6.QtWidgets import QFileDialog, QInputDialog

from . import scene_io

def reset_scene(win: Any) -> None:
    """Clear the current scene and create a new blank one."""
    scene_io.create_blank_scene(win, add_default_puppet=False)
    win.scene_controller.set_background_path(None)
    win.ensure_fit()


def set_background(win: Any) -> None:
    """Open a file dialog to choose a background image and apply it."""
    filePath: str
    filePath, _ = QFileDialog.getOpenFileName(
        win,
        "Charger une image d'arrière-plan",
        "",
        "Images (*.png *.jpg *.jpeg)",
    )
    if filePath:
        win.scene_controller.set_background_path(filePath)

def set_scene_size(win) -> None:
    """Prompt the user for scene width/height and apply to the scene.

    Updates the scene rect, visuals, background fit, and zoom status.
    """
    width, ok1 = QInputDialog.getInt(
        win,
        "Taille de la scène",
        "Largeur:",
        win.scene_model.scene_width,
        1,
    )
    if not ok1:
        return
    height, ok2 = QInputDialog.getInt(
        win,
        "Taille de la scène",
        "Hauteur:",
        win.scene_model.scene_height,
        1,
    )
    if not ok2:
        return

    # Déléguer au SceneController pour centraliser la logique
    try:
        win.scene_controller.set_scene_size(int(width), int(height))
    except (AttributeError, TypeError) as exc:
        logging.exception("SceneController set_scene_size failed")
        # Fallback en cas d'indisponibilité (sécurité)
        win.scene_model.scene_width = int(width)
        win.scene_model.scene_height = int(height)
        win.scene.setSceneRect(0, 0, int(width), int(height))
        win._update_scene_visuals()
        win._update_background()
        win._update_zoom_status()
