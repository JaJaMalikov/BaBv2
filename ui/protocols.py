from __future__ import annotations

"""Protocol interfaces for UI collaborators.

These protocols formalize expectations between controllers/adapters and UI widgets
without importing heavy Qt types at type-check time.

They intentionally keep attributes minimally typed to avoid runtime coupling.
"""

from typing import Any, Optional, Protocol, Tuple, Dict


class TimelineWidgetProtocol(Protocol):
    # Signals (Qt signals expose a .connect(callable) API); we type them as Any.
    playClicked: Any
    pauseClicked: Any
    stopClicked: Any
    loopToggled: Any
    fpsChanged: Any
    rangeChanged: Any
    frameChanged: Any
    addKeyframeClicked: Any
    deleteKeyframeClicked: Any
    copyKeyframeClicked: Any
    pasteKeyframeClicked: Any

    # Methods used by controllers/adapters
    def add_keyframe_marker(self, frame_index: int) -> None: ...
    def remove_keyframe_marker(self, frame_index: int) -> None: ...


class InspectorWidgetProtocol(Protocol):
    def sync_with_frame(self) -> None: ...


class ObjectViewAdapterProtocol(Protocol):
    # Capture of current UI state for model snapshotting
    def capture_puppet_states(self) -> Dict[str, Dict[str, Any]]: ...
    def capture_visible_object_states(self) -> Dict[str, Dict[str, Any]]: ...

    # Graphics management
    def add_object_graphics(self, obj: Any) -> None: ...
    def remove_object_graphics(self, name: str) -> None: ...
    def hide_object(self, name: str) -> None: ...

    # Object transform updates (return effective state snapshot)
    def set_object_scale(self, name: str, scale: float) -> Dict[str, Any]: ...
    def set_object_rotation(self, name: str, angle: float) -> Dict[str, Any]: ...
    def set_object_z(self, name: str, z: int) -> Dict[str, Any]: ...

    # Creation flows
    def create_object_from_file(
        self, file_path: str, scene_pos: Optional[Any] = None
    ) -> Optional[Tuple[Any, Dict[str, Any]]]: ...
    def create_light_object(
        self, scene_pos: Optional[Any] = None
    ) -> Optional[Tuple[Any, Dict[str, Any]]]: ...

    # Attachment flows return a state dict snapshot to persist
    def attach_object_to_member(
        self, obj_name: str, puppet_name: str, member_name: str
    ) -> Dict[str, Any]: ...
    def detach_object(self, obj_name: str) -> Dict[str, Any]: ...


class ZoomStatusAdapterProtocol(Protocol):
    """Adapter to decouple SceneView from MainWindow for zoom/scale updates.

    A thin layer that SceneView can call without knowing about QGraphicsView
    or MainWindow internals. This follows docs/tasks.md Task 6.
    """

    def scale_view(self, factor: float) -> None: ...
    def on_zoom_changed(self, zoom_factor: float) -> None: ...



class MessageAdapterProtocol(Protocol):
    """Adapter for user-facing messages/notifications from controllers or ops.

    UI can implement this using status bars, toast overlays, dialogs, etc.
    Levels are advisory: "info", "warning", "error".
    """

    def show_message(self, text: str, level: str = "info") -> None: ...
