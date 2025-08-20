from __future__ import annotations

"""Regroupe les interactions directes avec la ``QGraphicsScene``."""

from typing import TYPE_CHECKING, Optional
import logging

from PySide6.QtCore import QObject

from .scene_visuals import SceneVisuals
from ui.protocols import ZoomStatusAdapterProtocol

if TYPE_CHECKING:
    from .scene_controller import MainWindowProtocol


class SceneView(QObject):
    """Encapsule la logique liée à l'affichage de la scène."""

    def __init__(
        self,
        win: "MainWindowProtocol",
        visuals: Optional[SceneVisuals] | None = None,
        zoom_adapter: Optional[ZoomStatusAdapterProtocol] | None = None,
    ) -> None:
        super().__init__()
        self.win = win
        self.visuals: SceneVisuals = visuals if visuals is not None else SceneVisuals(win)
        self._zoom_adapter: Optional[ZoomStatusAdapterProtocol] = zoom_adapter
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
        # Notify zoom/scale status via adapter or compatibility callbacks
        try:
            if self._zoom_adapter is not None:
                self._zoom_adapter.on_zoom_changed(getattr(self.win, "zoom_factor", 1.0))
            else:
                callback = getattr(self.win, "on_zoom_changed", None)
                if callable(callback):
                    callback(getattr(self.win, "zoom_factor", 1.0))
                else:
                    # Backward-compatible fallback
                    getattr(self.win, "_update_zoom_status", lambda: None)()
        except Exception:
            logging.exception("Failed to notify zoom status after scene resize")

    def zoom(self, factor: float) -> None:
        """Applique un zoom sur la vue."""
        try:
            if self._zoom_adapter is not None:
                self._zoom_adapter.scale_view(factor)
            else:
                # Backward-compatible direct scale
                self.win.view.scale(factor, factor)
            # Maintain zoom factor on window if present
            if hasattr(self.win, "zoom_factor"):
                self.win.zoom_factor *= float(factor)
            # Notify status
            if self._zoom_adapter is not None:
                self._zoom_adapter.on_zoom_changed(getattr(self.win, "zoom_factor", 1.0))
            else:
                callback = getattr(self.win, "on_zoom_changed", None)
                if callable(callback):
                    callback(getattr(self.win, "zoom_factor", 1.0))
                else:
                    getattr(self.win, "_update_zoom_status", lambda: None)()
        except Exception:
            logging.exception("Failed to apply zoom")
