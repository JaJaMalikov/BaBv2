from __future__ import annotations

"""Service de lecture/lecture d'animation.

Gère le timer Qt, la navigation entre frames et un presse-papiers
simple pour les keyframes."""

from typing import Optional

from PySide6.QtCore import QObject, QTimer, Signal

from core.scene_model import SceneModel
from core.frame_math import compute_next_playback_frame


class PlaybackService(QObject):
    """Logique de lecture d'animation indépendante de la vue."""

    frame_update_requested = Signal()
    keyframe_add_requested = Signal(int)
    snapshot_requested = Signal(int)
    current_frame_changed = Signal(int)

    def __init__(
        self, scene_model: SceneModel, parent: Optional[QObject] = None
    ) -> None:
        super().__init__(parent)
        self.scene_model = scene_model
        self.playback_timer: QTimer = QTimer(self)
        self.playback_timer.timeout.connect(self.next_frame)
        self.set_fps(self.scene_model.fps)
        self.loop_enabled: bool = False
        self._kf_clipboard: Optional[dict] = None

    # --- Contrôle du timer -------------------------------------------------
    def play_animation(self) -> None:
        """Démarre le timer de lecture."""
        self.playback_timer.start()

    def pause_animation(self) -> None:
        """Met en pause la lecture."""
        self.playback_timer.stop()

    def stop_animation(self) -> None:
        """Arrête la lecture et revient au début de la plage."""
        self.playback_timer.stop()
        self.go_to_frame(self.scene_model.start_frame)

    def set_fps(self, fps: int) -> None:
        """Met à jour la cadence de lecture."""
        self.scene_model.fps = fps
        self.playback_timer.setInterval(1000 // fps if fps > 0 else 0)

    def set_range(self, start: int, end: int) -> None:
        """Définit les bornes de lecture."""
        self.scene_model.start_frame = start
        self.scene_model.end_frame = end

    # --- Navigation --------------------------------------------------------
    def next_frame(self) -> None:
        """Avance d'une frame en tenant compte du loop (centralisé)."""
        current = self.scene_model.current_frame
        start, end = self.scene_model.start_frame, self.scene_model.end_frame
        next_index, should_stop = compute_next_playback_frame(
            int(current), int(start), int(end), bool(self.loop_enabled)
        )
        if should_stop:
            self.pause_animation()
            self.current_frame_changed.emit(int(current))
            return
        self.go_to_frame(int(next_index))

    def go_to_frame(self, frame_index: int) -> None:
        """Déplace le modèle vers ``frame_index`` et émet les signaux adéquats."""
        if self.scene_model.current_frame == frame_index:
            self.scene_model.go_to_frame(frame_index)
            self.frame_update_requested.emit()
            self.current_frame_changed.emit(frame_index)
            return

        if self.scene_model.current_frame in self.scene_model.keyframes:
            self.snapshot_requested.emit(self.scene_model.current_frame)
        self.scene_model.go_to_frame(frame_index)
        self.frame_update_requested.emit()
        self.current_frame_changed.emit(frame_index)

    def delete_keyframe(self, frame_index: int) -> None:
        """Supprime une keyframe du modèle."""
        self.scene_model.remove_keyframe(frame_index)

    # --- Presse-papiers ----------------------------------------------------
    def copy_keyframe(self, frame_index: int) -> None:
        """Copie l'état exact d'une keyframe (centralisé)."""
        from controllers import keyframe_service as kfs

        self._kf_clipboard = kfs.copy_keyframe(self.scene_model, int(frame_index))

    def paste_keyframe(self, frame_index: int) -> None:
        """Colle l'état du presse-papiers à ``frame_index`` (centralisé)."""
        from controllers import keyframe_service as kfs

        if not kfs.paste_keyframe(
            self.scene_model, self._kf_clipboard, int(frame_index)
        ):
            return
        self.go_to_frame(int(frame_index))
        self.snapshot_requested.emit(int(frame_index))
