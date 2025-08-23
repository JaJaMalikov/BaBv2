"""Typed Protocols for UI/controller contracts.

Centralizes the structural types (duck-typed) used by controllers and views so we
can avoid pervasive Any and getattr. These protocols are used only for typing and
introduce no runtime coupling.

Notes
- Aligned with docs/plan.md and .junie/guidelines.md: controllers consume
  Protocols instead of concrete Qt widgets; views/adapters implement them.
- Tests may use fakes implementing these Protocols to validate controller logic
  without Qt (see tests/test_app_controller_shortcuts.py).
"""

from __future__ import annotations

from typing import Any, Dict, Protocol, runtime_checkable

# NOTE: We intentionally avoid importing Qt or project-heavy classes at runtime
# here to prevent circular imports. Keep types structural and minimal.


@runtime_checkable
class InspectorWidgetContract(Protocol):
    """Inspector widget contract used by controllers and adapters.

    Responsibilities:
    - Expose a refresh() method to repaint/update the inspector view.
    Usage:
    - Implemented by ui/views/inspector/InspectorWidget and fakes in tests.
    """

    def refresh(self) -> None: ...


@runtime_checkable
class TimelineWidgetContract(Protocol):
    """Timeline contract minimal surface.

    Responsibilities:
    - Manage keyframe markers and current frame display.
    Usage:
    - Implemented by ui/views/timeline_widget.py and fakes in tests.
    """

    def clear_keyframes(self) -> None: ...
    def add_keyframe_marker(self, index: int) -> None: ...
    def set_current_frame(self, index: int) -> None: ...


@runtime_checkable
class PlaybackHandlerContract(Protocol):
    """Playback/keyframe interaction surface consumed by controllers."""

    def copy_keyframe(self, index: int) -> None: ...
    def paste_keyframe(self, index: int) -> None: ...
    def update_timeline_ui_from_model(self) -> None: ...


@runtime_checkable
class ObjectViewAdapterContract(Protocol):
    """Adapter over scene object graphics used by controllers.

    Purpose:
    - Bridge Qt graphics (items/renderers) and controller-friendly state dicts.
    - Provide capture and lifecycle helpers without leaking Qt types to controllers.
    Implementations:
    - ui/object_view_adapter.py and fakes in tests.
    """

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
    def create_object_from_file(
        self, file_path: str, scene_pos: Any | None = None
    ) -> tuple[Any, Dict[str, Any]] | None: ...
    def create_light_object(
        self, scene_pos: Any | None = None
    ) -> tuple[Any, Dict[str, Any]] | None: ...

    # Attachment APIs return a fresh state dict applied to the model
    def attach_object_to_member(
        self, obj_name: str, puppet_name: str, member_name: str
    ) -> Dict[str, Any]: ...
    def detach_object(self, obj_name: str) -> Dict[str, Any]: ...


@runtime_checkable
class SceneModelContract(Protocol):
    """Pure model contract (no Qt types) consumed by controllers/services.

    The concrete implementation lives in core/scene_model.py and must remain
    free of PySide/Qt dependencies. Controllers access only this minimal surface.
    """

    # Attributes commonly used by controllers/services
    start_frame: int
    end_frame: int
    current_frame: int
    scene_width: int
    scene_height: int
    fps: int
    keyframes: Dict[int, Any]
    puppets: Dict[str, Any]
    objects: Dict[str, Any]

    # Minimal mutation/navigation surface
    def add_keyframe(self, index: int, state: Dict[str, Any]) -> None: ...
    def remove_keyframe(self, index: int) -> None: ...
    def go_to_frame(self, index: int) -> None: ...

    # Object/puppet management
    def add_object(self, obj: Any) -> None: ...
    def remove_object(self, name: str) -> None: ...
    def add_puppet(self, name: str, puppet: Any) -> None: ...
    def remove_puppet(self, name: str) -> None: ...

    # Serialization
    def to_dict(self) -> Dict[str, Any]: ...
    def from_dict(self, data: Dict[str, Any]) -> None: ...


@runtime_checkable
class AppWindowContract(Protocol):
    """Main application window surface consumed by AppController.

    Exposes typed attributes for key components and helper methods used during
    startup and runtime. Implemented by ui/main_window.MainWindow and fakes in tests.
    """

    # Widgets / components referenced by AppController
    view: "SceneViewProtocol"
    timeline_dock: Any
    timeline_widget: TimelineWidgetContract
    scene_model: SceneModelContract
    playback_handler: PlaybackHandlerContract
    object_view_adapter: ObjectViewAdapterContract
    scene_controller: Any
    controller: Any
    scene: Any  # QGraphicsScene-like with selectionChanged signal

    # Optional shortcuts used by AppController (may be missing in tests)
    _kf_copy_sc: Any
    _kf_paste_sc: Any

    # Methods
    def showMaximized(self) -> None: ...
    def ensure_fit(self) -> None: ...
    def update_onion_skins(self) -> None: ...


@runtime_checkable
class SceneWindowContract(Protocol):
    """Contract for the window owning the scene view and related components.

    Used by SceneController for operations requiring access to scene/view/adapters
    without tying to concrete Qt widgets.
    """

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


# The following Protocols provide commonly-referenced names used in docs/tasks.md
# They are aliases/minimal surfaces over existing *Contract types for clarity.
@runtime_checkable
class SceneViewProtocol(Protocol):
    """Minimal scene view surface used by controllers/adapters in tests & runtime."""

    # Minimal API surface commonly exercised by controllers and tests
    def set_background(self, bg: dict | str | None) -> None: ...
    def set_zoom(self, factor: float) -> None: ...
    def center_on_selection(self) -> None: ...
    def refresh(self) -> None: ...

    # Overlay/menu application hooks (SettingsManager/OverlayManager)
    def apply_menu_settings_main(self) -> None: ...
    def apply_menu_settings_quick(self) -> None: ...


@runtime_checkable
class TimelineViewProtocol(TimelineWidgetContract, Protocol):
    """Alias protocol for timeline widget used by controllers/tests."""

    pass


@runtime_checkable
class InspectorProtocol(InspectorWidgetContract, Protocol):
    """Alias protocol for inspector widget used by controllers/tests."""

    pass


@runtime_checkable
class MainWindowProtocol(AppWindowContract, Protocol):
    """Alias protocol for main window used by AppController and tests."""

    pass
