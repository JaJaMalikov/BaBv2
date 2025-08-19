"""Coordonne la lecture entre service et vue."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, Signal

from core.scene_model import SceneModel
from controllers.playback_service import PlaybackService
from ui.playback_view_adapter import PlaybackViewAdapter
from ui.views.timeline_widget import TimelineWidget
from ui.views.inspector.inspector_widget import InspectorWidget


class PlaybackController(QObject):
    """Orchestrateur entre le ``PlaybackService`` et la vue timeline."""

    frame_update_requested = Signal()
    keyframe_add_requested = Signal(int)
    snapshot_requested = Signal(int)

    def __init__(
        self,
        scene_model: SceneModel,
        timeline_widget: TimelineWidget,
        inspector_widget: InspectorWidget,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._service = PlaybackService(scene_model, parent)
        self._timeline = timeline_widget
        self._view = PlaybackViewAdapter(timeline_widget, inspector_widget, self._service, parent)

        # Propager les signaux du service
        self._service.frame_update_requested.connect(self.frame_update_requested)
        self._service.keyframe_add_requested.connect(self.keyframe_add_requested)
        self._service.snapshot_requested.connect(self.snapshot_requested)
        self._service.current_frame_changed.connect(self._timeline.set_current_frame)

    # --- Délégations au service -------------------------------------------
    def play_animation(self) -> None:
        self._service.play_animation()

    def pause_animation(self) -> None:
        self._service.pause_animation()

    def stop_animation(self) -> None:
        self._service.stop_animation()

    def next_frame(self) -> None:
        self._service.next_frame()

    def set_fps(self, fps: int) -> None:
        self._service.set_fps(fps)

    def set_range(self, start: int, end: int) -> None:
        self._service.set_range(start, end)

    def go_to_frame(self, frame_index: int) -> None:
        self._service.go_to_frame(frame_index)

    def delete_keyframe(self, frame_index: int) -> None:
        self._service.delete_keyframe(frame_index)
        self._timeline.remove_keyframe_marker(frame_index)

    def copy_keyframe(self, frame_index: int) -> None:
        self._service.copy_keyframe(frame_index)

    def paste_keyframe(self, frame_index: int) -> None:
        self._service.paste_keyframe(frame_index)
        self._timeline.add_keyframe_marker(frame_index)

    def update_timeline_ui_from_model(self) -> None:
        """Met à jour le widget timeline à partir du modèle."""
        self._timeline.fps_spinbox.setValue(self._service.scene_model.fps)
        self._timeline.start_frame_spinbox.setValue(self._service.scene_model.start_frame)
        self._timeline.end_frame_spinbox.setValue(self._service.scene_model.end_frame)
        self._timeline.slider.setRange(
            self._service.scene_model.start_frame,
            self._service.scene_model.end_frame,
        )
