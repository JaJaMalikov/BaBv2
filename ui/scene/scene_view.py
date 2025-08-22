from __future__ import annotations

"""Regroupe les interactions directes avec la ``QGraphicsScene``."""

from typing import Any
import logging

from PySide6.QtCore import QObject

from .scene_visuals import SceneVisuals


class SceneView(QObject):
    """Encapsule la logique liée à l'affichage de la scène."""

    def __init__(self, win: Any, visuals: SceneVisuals | None = None) -> None:
        super().__init__()
        self.win = win
        self.visuals: SceneVisuals = (
            visuals if visuals is not None else SceneVisuals(win)
        )
        if visuals is None:
            self.visuals.setup()

    # ------------------------------------------------------------------
    def update_scene_visuals(self) -> None:
        """Met à jour les éléments graphiques de la scène."""
        self.visuals.update_scene_visuals()

    def update_background(self, _path: object | None = None) -> None:
        """Met à jour l'arrière-plan de la scène."""
        self.visuals.update_background()

    def handle_scene_resized(self, width: int, height: int) -> None:
        """Applique une nouvelle taille de scène au ``QGraphicsScene``."""
        self.win.scene.setSceneRect(0, 0, int(width), int(height))
        self.update_scene_visuals()
        self.update_background()
        try:
            self.win._update_zoom_status()
        except (RuntimeError, AttributeError):
            logging.exception("Failed to update zoom status after scene resize")

    def zoom(self, factor: float) -> None:
        """Applique un zoom sur la vue."""
        self.win.view.scale(factor, factor)
        self.win.zoom_factor *= factor
        try:
            self.win._update_zoom_status()
        except (RuntimeError, AttributeError):
            logging.exception("Failed to update zoom status")
