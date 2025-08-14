"""Module for handling playback and timeline interactions."""

from PySide6.QtCore import QObject, QTimer, Signal

from typing import Optional

from core.scene_model import SceneModel
from ui.timeline_widget import TimelineWidget
from ui.inspector_widget import InspectorWidget


class PlaybackHandler(QObject):
    """
    Manages playback, timeline state, and keyframe operations.
    Decouples timeline logic from the main window.
    """
    frame_update_requested = Signal()
    keyframe_add_requested = Signal(int)
    snapshot_requested = Signal(int)

    def __init__(self, scene_model: SceneModel, timeline_widget: TimelineWidget, inspector_widget: InspectorWidget, parent: Optional[QObject] = None) -> None:
        """Initializes the playback handler.

        Args:
            scene_model: The scene model.
            timeline_widget: The timeline widget.
            inspector_widget: The inspector widget.
            parent: The parent object.
        """
        super().__init__(parent)
        self.scene_model: SceneModel = scene_model
        self.timeline_widget: TimelineWidget = timeline_widget
        self.inspector_widget: InspectorWidget = inspector_widget

        self.playback_timer: QTimer = QTimer(self)
        self.playback_timer.timeout.connect(self.next_frame)
        self.set_fps(self.scene_model.fps)

        self._connect_signals()

    def _connect_signals(self) -> None:
        """Connects signals from the timeline widget to the handler's slots."""
        # Connect to timeline widget signals
        self.timeline_widget.playClicked.connect(self.play_animation)
        self.timeline_widget.pauseClicked.connect(self.pause_animation)
        self.timeline_widget.stopClicked.connect(self.stop_animation)
        self.timeline_widget.loopToggled.connect(self._on_loop_toggled)
        self.timeline_widget.fpsChanged.connect(self.set_fps)
        self.timeline_widget.rangeChanged.connect(self.set_range)
        self.timeline_widget.frameChanged.connect(self.go_to_frame)
        self.timeline_widget.addKeyframeClicked.connect(self.keyframe_add_requested)
        self.timeline_widget.deleteKeyframeClicked.connect(self.delete_keyframe)

        # Sync inspector
        self.timeline_widget.frameChanged.connect(self.inspector_widget.sync_with_frame)

    def play_animation(self) -> None:
        """Starts the playback timer."""
        self.playback_timer.start()

    def pause_animation(self) -> None:
        """Stops the playback timer."""
        self.playback_timer.stop()

    def stop_animation(self) -> None:
        """Stops the playback timer and resets the current frame to the start frame."""
        self.playback_timer.stop()
        self.timeline_widget.set_current_frame(self.scene_model.start_frame)

    def next_frame(self) -> None:
        """Advances to the next frame in the animation."""
        current: int = self.scene_model.current_frame
        start: int
        end: int
        start, end = self.scene_model.start_frame, self.scene_model.end_frame
        new_frame: int = current + 1
        if new_frame > end:
            if self.timeline_widget.loop_enabled:
                new_frame = start
            else:
                self.pause_animation()
                self.timeline_widget.play_btn.setChecked(False)
                return
        self.timeline_widget.set_current_frame(new_frame)

    def _on_loop_toggled(self, enabled: bool):
        """Handles the loop toggled signal from the timeline widget."""
        self.timeline_widget.loop_enabled = enabled

    def set_fps(self, fps: int) -> None:
        """Sets the frames per second for playback."""
        self.scene_model.fps = fps
        self.playback_timer.setInterval(1000 // fps if fps > 0 else 0)

    def set_range(self, start: int, end: int) -> None:
        """Sets the start and end frames for playback."""
        self.scene_model.start_frame = start
        self.scene_model.end_frame = end

    def go_to_frame(self, frame_index: int):
        """Goes to a specific frame in the timeline."""
        # Request a snapshot of the current frame before changing, but only if it is a keyframe
        if self.scene_model.current_frame in self.scene_model.keyframes:
            self.snapshot_requested.emit(self.scene_model.current_frame)
        self.scene_model.go_to_frame(frame_index)
        self.frame_update_requested.emit()

    def delete_keyframe(self, frame_index: int):
        """Deletes a keyframe from the timeline."""
        self.scene_model.remove_keyframe(frame_index)
        self.timeline_widget.remove_keyframe_marker(frame_index)

    def update_timeline_ui_from_model(self) -> None:
        """Updates the timeline widget with the current scene model values."""
        self.timeline_widget.fps_spinbox.setValue(self.scene_model.fps)
        self.timeline_widget.start_frame_spinbox.setValue(self.scene_model.start_frame)
        self.timeline_widget.end_frame_spinbox.setValue(self.scene_model.end_frame)
        self.timeline_widget.slider.setRange(self.scene_model.start_frame, self.scene_model.end_frame)
