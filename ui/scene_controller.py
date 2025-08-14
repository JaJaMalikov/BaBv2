"""SceneController: façade légère pour regrouper les opérations de scène.

Objectif de ce premier incrément:
- Centraliser l'accès à StateApplier, SceneVisuals et OnionSkinManager
- Exposer de petites méthodes de délégation sans changer le comportement
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.puppet_piece import PuppetPiece
from ui.state_applier import StateApplier
from ui.scene_visuals import SceneVisuals
from ui.onion_skin import OnionSkinManager


class SceneController:
    """A facade for grouping scene operations."""
    def __init__(self, win: Any, *, visuals: SceneVisuals | None = None, onion: OnionSkinManager | None = None, applier: StateApplier | None = None) -> None:
        """Initializes the scene controller.

        Args:
            win: The main window of the application.
            visuals: The scene visuals manager.
            onion: The onion skin manager.
            applier: The state applier.
        """
        self.win = win
        # Conserver les instances existantes si fournies pour éviter tout double initialisation
        self.visuals: SceneVisuals = visuals if visuals is not None else SceneVisuals(win)
        # S'assurer que setup est appelé si la visualisation est créée ici
        if visuals is None:
            self.visuals.setup()

        self.onion: OnionSkinManager = onion if onion is not None else OnionSkinManager(win)
        self.applier: StateApplier = applier if applier is not None else StateApplier(win)

    # --- Délégations visuelles ---
    def update_scene_visuals(self) -> None:
        """Updates the scene visuals."""
        self.visuals.update_scene_visuals()

    def update_background(self) -> None:
        """Updates the background."""
        self.visuals.update_background()
    def set_background_path(self, path: Optional[str]) -> None:
        """Set background image path and refresh visuals accordingly."""
        self.win.scene_model.background_path = path
        self.update_background()
	# --- Zoom & ajustements de vue ---
    def zoom(self, factor: float) -> None:
        """Applique un zoom sur la vue et met à jour le statut."""
        self.win.view.scale(factor, factor)
        self.win.zoom_factor *= factor
        try:
            self.win._update_zoom_status()
        except Exception:
            pass

    # --- Délégations onion skin ---
    def set_onion_enabled(self, enabled: bool) -> None:
        """Enables or disables onion skinning."""
        self.onion.set_enabled(enabled)

    def clear_onion_skins(self) -> None:
        """Clears the onion skins."""
        self.onion.clear()

    def update_onion_skins(self) -> None:
        """Updates the onion skins."""
        self.onion.update()

    # --- Poignées de rotation ---
    def set_rotation_handles_visible(self, visible: bool) -> None:
        """Afficher ou masquer les poignées de rotation des pantins."""
        for item in self.win.object_manager.graphics_items.values():
            if isinstance(item, PuppetPiece):
                item.set_handle_visibility(visible)
        try:
            self.win.view.handles_btn.setChecked(visible)
        except Exception:
            pass

    # --- Application d'états (keyframes) ---
    def apply_puppet_states(self, graphics_items: Dict[str, Any], keyframes: Dict[int, Any], index: int) -> None:
        """Applies puppet states from a keyframe to the scene."""
        self.applier.apply_puppet_states(graphics_items, keyframes, index)

    def apply_object_states(self, graphics_items: Dict[str, Any], keyframes: Dict[int, Any], index: int) -> None:
        """Applies object states from a keyframe to the scene."""
        self.applier.apply_object_states(graphics_items, keyframes, index)

    # --- Réglages scène ---
    def set_scene_size(self, width: int, height: int) -> None:
        """Ajuste la taille de la scène et rafraîchit les visuels.

        Conserve le comportement historique: met à jour la rect, rafraîchit visuels,
        relance l'arrière-plan (qui peut réimposer une taille selon l'image) et met à jour le zoom.
        """
        self.win.scene_model.scene_width = int(width)
        self.win.scene_model.scene_height = int(height)
        self.win.scene.setSceneRect(0, 0, int(width), int(height))
        self.update_scene_visuals()
        self.update_background()
        try:
            self.win._update_zoom_status()
        except Exception:
            pass
