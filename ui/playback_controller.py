from __future__ import annotations

"""PlaybackController: façade légère autour de PlaybackHandler.

Expose les mêmes signaux et méthodes clés afin d'alléger MainWindow et
préparer d'éventuelles évolutions (renommage/extension) sans impacter le reste.
"""

from typing import Optional
from PySide6.QtCore import QObject, Signal

from core.scene_model import SceneModel
from ui.timeline_widget import TimelineWidget
from ui.inspector_widget import InspectorWidget
from ui.playback_handler import PlaybackHandler


class PlaybackController(QObject):
    # Re-exposed signals
    frame_update_requested = Signal()
    keyframe_add_requested = Signal(int)
    snapshot_requested = Signal(int)

    def __init__(self, scene_model: SceneModel, timeline_widget: TimelineWidget, inspector_widget: InspectorWidget, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._handler = PlaybackHandler(scene_model, timeline_widget, inspector_widget, parent)
        # Forward signals
        self._handler.frame_update_requested.connect(self.frame_update_requested)
        self._handler.keyframe_add_requested.connect(self.keyframe_add_requested)
        self._handler.snapshot_requested.connect(self.snapshot_requested)

    # Thin delegations to underlying handler
    def play_animation(self) -> None: self._handler.play_animation()
    def pause_animation(self) -> None: self._handler.pause_animation()
    def stop_animation(self) -> None: self._handler.stop_animation()
    def next_frame(self) -> None: self._handler.next_frame()
    def set_fps(self, fps: int) -> None: self._handler.set_fps(fps)
    def set_range(self, start: int, end: int) -> None: self._handler.set_range(start, end)
    def go_to_frame(self, frame_index: int) -> None: self._handler.go_to_frame(frame_index)
    def delete_keyframe(self, frame_index: int) -> None: self._handler.delete_keyframe(frame_index)
    def update_timeline_ui_from_model(self) -> None: self._handler.update_timeline_ui_from_model()

