"""Typed Protocols for UI/controller contracts.

Centralizes the structural types (duck-typed) used by controllers and views so we
can avoid pervasive Any and getattr. These protocols are used only for typing and
introduce no runtime coupling.
"""

from __future__ import annotations

from typing import Any, Dict, Protocol, runtime_checkable

# NOTE: We intentionally avoid importing Qt or project-heavy classes at runtime
# here to prevent circular imports. Keep types structural and minimal.


@runtime_checkable
class InspectorWidgetContract(Protocol):
    def refresh(self) -> None: ...


@runtime_checkable
class TimelineWidgetContract(Protocol):
    def clear_keyframes(self) -> None: ...
    def add_keyframe_marker(self, index: int) -> None: ...
    def set_current_frame(self, index: int) -> None: ...


@runtime_checkable
class PlaybackHandlerContract(Protocol):
    def copy_keyframe(self, index: int) -> None: ...
    def paste_keyframe(self, index: int) -> None: ...
    def update_timeline_ui_from_model(self) -> None: ...


@runtime_checkable
class ObjectViewAdapterContract(Protocol):
    # Map of object name -> QGraphicsItem-like objects
    graphics_items: Dict[str, Any]
    # Optional renderer cache; keep loose typing here
    renderers: Dict[str, Any]

    # State capture APIs used by controllers
    def capture_puppet_states(self) -> Dict[str, Dict[str, Any]]: ...
    def capture_visible_object_states(self) -> Dict[str, Dict[str, Any]]: ...
    def read_item_state(self, name: str) -> Dict[str, Any]: ...

    # Graphics/object lifecycle APIs
    def add_object_graphics(self, obj: Any) -> None: ...
    def remove_object_graphics(self, name: str) -> None: ...
    def hide_object(self, name: str) -> None: ...

    # Creation helpers return (SceneObject-like, state) or None
    def create_object_from_file(self, file_path: str, scene_pos: Any | None = None) -> tuple[Any, Dict[str, Any]] | None: ...
    def create_light_object(self, scene_pos: Any | None = None) -> tuple[Any, Dict[str, Any]] | None: ...

    # Attachment APIs return a fresh state dict applied to the model
    def attach_object_to_member(self, obj_name: str, puppet_name: str, member_name: str) -> Dict[str, Any]: ...
    def detach_object(self, obj_name: str) -> Dict[str, Any]: ...


@runtime_checkable
class SceneModelContract(Protocol):
    # Only the attributes needed by controllers
    start_frame: int
    current_frame: int
    scene_width: int
    scene_height: int
    keyframes: Dict[int, Any]
    puppets: Dict[str, Any]
    objects: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]: ...
    def from_dict(self, data: Dict[str, Any]) -> None: ...


@runtime_checkable
class AppWindowContract(Protocol):
    # Widgets / components referenced by AppController
    timeline_dock: Any
    timeline_widget: TimelineWidgetContract
    scene_model: SceneModelContract
    playback_handler: PlaybackHandlerContract
    object_view_adapter: ObjectViewAdapterContract
    scene_controller: Any
    controller: Any
    scene: Any  # QGraphicsScene-like with selectionChanged signal

    # Methods
    def showMaximized(self) -> None: ...
    def ensure_fit(self) -> None: ...
    def update_onion_skins(self) -> None: ...


@runtime_checkable
class SceneWindowContract(Protocol):
    # Minimal surface used by SceneController
    scene: Any
    scene_model: SceneModelContract
    object_manager: ObjectViewAdapterContract
    view: Any
    zoom_factor: float
    _suspend_item_updates: bool
    inspector_widget: InspectorWidgetContract

    controller: Any
    object_controller: Any
    playback_handler: PlaybackHandlerContract
    timeline_widget: TimelineWidgetContract

    # Private UI helpers (Qt-side), referenced indirectly
    def _update_background(self) -> None: ...
    def _update_zoom_status(self) -> None: ...
