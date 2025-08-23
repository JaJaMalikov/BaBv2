"""Application controller orchestrating the MainWindow and SceneModel."""

from __future__ import annotations

import logging

from ui import selection_sync
from ui.scene import scene_io
from ui.contracts import AppWindowContract

logger = logging.getLogger(__name__)


class AppController:
    """Centralise la logique métier autour de la `MainWindow`."""

    def __init__(self, win: AppWindowContract) -> None:
        self.win = win
        self._install_shortcuts()

    # --- Initialisation -------------------------------------------------
    def startup_sequence(self) -> None:
        """Lance la séquence de démarrage de l'interface."""
        self.win.showMaximized()
        self.win.timeline_dock.show()
        self.win.timeline_dock.visibilityChanged.connect(
            lambda _: self.win.ensure_fit()
        )
        self.win.timeline_dock.topLevelChanged.connect(lambda _: self.win.ensure_fit())
        self.win.ensure_fit()
        scene_io.create_blank_scene(self.win)
        self.win.ensure_fit()
        self.win.scene.selectionChanged.connect(self.on_scene_selection_changed)

    # --- Raccourcis globaux --------------------------------------------
    def _install_shortcuts(self) -> None:
        """Connecte les raccourcis de copie/collage de pose."""
        try:
            self.win._kf_copy_sc.activated.connect(self.copy_current_keyframe)
            self.win._kf_paste_sc.activated.connect(self.paste_current_keyframe)
        except (AttributeError, RuntimeError) as e:
            logger.warning("Failed to install keyframe shortcuts: %s", e, exc_info=True)

    def copy_current_keyframe(self) -> None:
        """Copie le keyframe courant via le `PlaybackController`."""
        try:
            idx = int(self.win.scene_model.current_frame)
            if idx in getattr(self.win.timeline_widget, "_kfs", set()):
                self.win.playback_handler.copy_keyframe(idx)  # type: ignore[attr-defined]
        except (AttributeError, ValueError, RuntimeError, TypeError) as e:
            logger.debug("Copy current keyframe shortcut ignored: %s", e)

    def paste_current_keyframe(self) -> None:
        """Colle le keyframe courant via le `PlaybackController`."""
        try:
            idx = int(self.win.scene_model.current_frame)
            self.win.playback_handler.paste_keyframe(idx)  # type: ignore[attr-defined]
        except (AttributeError, ValueError, RuntimeError, TypeError) as e:
            logger.debug("Paste current keyframe shortcut ignored: %s", e)

    # --- Manipulation de keyframes ------------------------------------
    def add_keyframe(self, frame_index: int) -> None:
        """Ajoute un keyframe en capturant l'état courant de la scène."""
        self.win.scene_controller.service.add_keyframe(frame_index)
        self.win.timeline_widget.add_keyframe_marker(frame_index)

    def update_scene_from_model(self) -> None:
        """Applique l'état du modèle à la scène graphique via un point d'entrée unique."""
        from controllers import state_applier

        logging.debug(
            "update_scene_from_model: frame=%s, keyframes=%s",
            self.win.scene_model.current_frame,
            (
                list(self.win.scene_model.keyframes.keys())
                if self.win.scene_model.keyframes
                else []
            ),
        )
        state_applier.apply_frame(self.win)

    # --- Synchronisation scène/inspecteur ------------------------------
    def select_object_in_inspector(self, name: str) -> None:
        """Sélectionne un objet dans l'inspecteur."""
        selection_sync.select_object_in_inspector(self.win, name)

    def on_scene_selection_changed(self) -> None:
        """Réagit aux changements de sélection dans la scène."""
        selection_sync.scene_selection_changed(self.win)

    def on_frame_update(self) -> None:
        """Met à jour la scène après un changement de frame."""
        self.update_scene_from_model()
        self.win.update_onion_skins()
