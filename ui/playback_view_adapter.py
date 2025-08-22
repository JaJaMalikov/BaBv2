from __future__ import annotations

"""Adaptateur de vue pour la lecture.

Relie les signaux du ``TimelineWidget`` aux appels du ``PlaybackService``.
"""

from typing import Optional

from PySide6.QtCore import QObject

from controllers.playback_service import PlaybackService
from ui.views.timeline_widget import TimelineWidget
from ui.views.inspector.inspector_widget import InspectorWidget


class PlaybackViewAdapter(QObject):
    """Connecte la vue au service de lecture."""

    def __init__(
        self,
        timeline_widget: TimelineWidget,
        inspector_widget: InspectorWidget,
        service: PlaybackService,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.timeline_widget = timeline_widget
        self.inspector_widget = inspector_widget
        self.service = service
        self._connect_signals()

    # ------------------------------------------------------------------
    def _connect_signals(self) -> None:
        tw = self.timeline_widget
        tw.playClicked.connect(self.service.play_animation)
        tw.pauseClicked.connect(self.service.pause_animation)
        tw.stopClicked.connect(self.service.stop_animation)
        tw.loopToggled.connect(self._on_loop_toggled)
        tw.fpsChanged.connect(self.service.set_fps)
        tw.rangeChanged.connect(self.service.set_range)
        tw.frameChanged.connect(self.service.go_to_frame)
        tw.frameChanged.connect(self.inspector_widget.sync_with_frame)
        tw.addKeyframeClicked.connect(self.service.keyframe_add_requested)
        tw.deleteKeyframeClicked.connect(self._on_delete_keyframe)
        tw.copyKeyframeClicked.connect(self.service.copy_keyframe)
        tw.pasteKeyframeClicked.connect(self._on_paste_keyframe)

    def _on_loop_toggled(self, enabled: bool) -> None:
        self.service.loop_enabled = enabled

    def _on_delete_keyframe(self, frame_index: int) -> None:
        self.service.delete_keyframe(frame_index)
        self.timeline_widget.remove_keyframe_marker(frame_index)

    def _on_paste_keyframe(self, frame_index: int) -> None:
        self.service.paste_keyframe(frame_index)
        self.timeline_widget.add_keyframe_marker(frame_index)
