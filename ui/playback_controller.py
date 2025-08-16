"""PlaybackController: A lightweight facade for PlaybackHandler.

This module provides a facade around the PlaybackHandler, exposing the same key
signals and methods. This helps to simplify MainWindow and allows for future
modifications (renaming/extending) without impacting the rest of the application.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, Signal

from core.scene_model import SceneModel
from ui.inspector.inspector_widget import InspectorWidget
from ui.playback_handler import PlaybackHandler
from ui.timeline_widget import TimelineWidget


class PlaybackController(QObject):
    """A facade around PlaybackHandler, exposing key signals and methods for controlling animation playback."""

    # Re-exposed signals
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
        """Initializes the playback controller.

        Args:
            scene_model: The scene model.
            timeline_widget: The timeline widget.
            inspector_widget: The inspector widget.
            parent: The parent object.
        """
        super().__init__(parent)
        self._handler = PlaybackHandler(
            scene_model, timeline_widget, inspector_widget, parent
        )
        # Forward signals
        self._handler.frame_update_requested.connect(self.frame_update_requested)
        self._handler.keyframe_add_requested.connect(self.keyframe_add_requested)
        self._handler.snapshot_requested.connect(self.snapshot_requested)

    # Thin delegations to underlying handler
    def play_animation(self) -> None:
        """Plays the animation."""
        self._handler.play_animation()

    def pause_animation(self) -> None:
        """Pauses the animation."""
        self._handler.pause_animation()

    def stop_animation(self) -> None:
        """Stops the animation."""
        self._handler.stop_animation()

    def next_frame(self) -> None:
        """Goes to the next frame."""
        self._handler.next_frame()

    def set_fps(self, fps: int) -> None:
        """Sets the FPS."""
        self._handler.set_fps(fps)

    def set_range(self, start: int, end: int) -> None:
        """Sets the frame range."""
        self._handler.set_range(start, end)

    def go_to_frame(self, frame_index: int) -> None:
        """Goes to a specific frame."""
        self._handler.go_to_frame(frame_index)

    def delete_keyframe(self, frame_index: int) -> None:
        """Deletes a keyframe."""
        self._handler.delete_keyframe(frame_index)

    def update_timeline_ui_from_model(self) -> None:
        """Updates the timeline UI from the model."""
        self._handler.update_timeline_ui_from_model()