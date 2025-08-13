from __future__ import annotations

from typing import Any
from PySide6.QtWidgets import QFileDialog

import ui.scene_io as scene_io


def reset_scene(win: Any) -> None:
    """Clear the current scene and create a new blank one."""
    scene_io.create_blank_scene(win, add_default_puppet=False)
    win.scene_model.background_path = None
    win._update_background()
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
        win.scene_model.background_path = filePath
        win._update_background()

