"""SceneController: façade légère regroupant les opérations de scène."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional, Protocol, cast

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene

from core.scene_model import Keyframe, SceneModel, SceneObject
from controllers.scene_service import SceneService
from .state_applier import StateApplier
from .scene_view import SceneView
from ..onion_skin import OnionSkinManager
from .puppet_ops import PuppetOps
from .library_ops import LibraryOps, LibraryPayload

if TYPE_CHECKING:
    from ..object_view_adapter import ObjectViewAdapter
    from ..zoomable_view import ZoomableView


class InspectorWidgetProtocol(Protocol):
    """Protocol describing the interface expected from the inspector widget."""

    def refresh(self) -> None:
        """Refresh the inspector's displayed information."""


class MainWindowProtocol(Protocol):
    """Minimal protocol for the main window used by scene operations."""

    scene: QGraphicsScene
    scene_model: SceneModel
    object_manager: ObjectViewAdapter
    view: ZoomableView
    zoom_factor: float
    _suspend_item_updates: bool
    inspector_widget: InspectorWidgetProtocol

    controller: Any

    def _update_background(self) -> None: ...

    def _update_zoom_status(self) -> None: ...


class SceneController:
    """Facade orchestrating scene-related operations."""

    def __init__(
        self,
        win: MainWindowProtocol,
        *,
        service: SceneService | None = None,
        view: SceneView | None = None,
        onion: OnionSkinManager | None = None,
        applier: StateApplier | None = None,
    ) -> None:
        """Initialize the scene controller."""
        self.win = win
        self.service = service if service is not None else SceneService(
            win.scene_model, win.object_controller.capture_scene_state
        )
        self.view = view if view is not None else SceneView(win)
        self.onion: OnionSkinManager = (
            onion if onion is not None else OnionSkinManager(win)
        )
        self.applier: StateApplier = (
            applier if applier is not None else StateApplier(win)
        )
        self.puppet_ops = PuppetOps(win, self.service)
        self.library_ops = LibraryOps(
            win, self.puppet_ops, win.object_controller, self.service
        )
        self.service.background_changed.connect(self.view.update_background)
        self.service.scene_resized.connect(self.view.handle_scene_resized)

    # --- Puppet operations -------------------------------------------------
    def add_puppet(self, file_path: str, puppet_name: str) -> None:
        """Add a puppet to the scene."""
        self.puppet_ops.add_puppet(file_path, puppet_name)

    def scale_puppet(self, puppet_name: str, ratio: float) -> None:
        """Scale a puppet by the given ratio."""
        self.puppet_ops.scale_puppet(puppet_name, ratio)

    def delete_puppet(self, puppet_name: str) -> None:
        """Delete a puppet from the scene."""
        self.puppet_ops.delete_puppet(puppet_name)

    def duplicate_puppet(self, puppet_name: str) -> None:
        """Duplicate a puppet."""
        self.puppet_ops.duplicate_puppet(puppet_name)

    def get_puppet_rotation(self, puppet_name: str) -> float:
        """Return the current rotation of a puppet."""
        return cast(float, self.puppet_ops.get_puppet_rotation(puppet_name))

    def set_puppet_rotation(self, puppet_name: str, angle: float) -> None:
        """Set the rotation angle of a puppet."""
        self.puppet_ops.set_puppet_rotation(puppet_name, angle)

    def set_puppet_z_offset(self, puppet_name: str, offset: int) -> None:
        """Set the Z offset of a puppet."""
        self.puppet_ops.set_puppet_z_offset(puppet_name, offset)

    def set_rotation_handles_visible(self, visible: bool) -> None:
        """Toggle visibility of rotation handles."""
        self.puppet_ops.set_rotation_handles_visible(visible)

    # --- Variants ---------------------------------------------------------
    def set_member_variant(
        self, puppet_name: str, slot: str, variant_name: str
    ) -> None:
        """Choose a variant for a puppet slot at the current frame.

        - Immediately updates scene visibility
        - Ensures a keyframe exists and records the choice under puppets[puppet]["_variants"].
        """
        # Update visuals immediately
        self.puppet_ops.set_member_variant(puppet_name, slot, variant_name)
        self.service.set_member_variant(puppet_name, slot, variant_name)
        try:
            self.win.controller.update_scene_from_model()
            self.win.update_onion_skins()
        except (RuntimeError, AttributeError):
            logging.exception("Failed to refresh scene after variant change")

    # --- Object operations -------------------------------------------------
    def delete_object(self, name: str) -> None:
        """Delete an object."""
        self.win.object_controller.remove_object(name)

    def duplicate_object(self, name: str) -> None:
        """Duplicate an object."""
        self.win.object_controller.duplicate_object(name)

    def attach_object_to_member(
        self, obj_name: str, puppet_name: str, member_name: str
    ) -> None:
        """Attach an object to a puppet member."""
        self.win.object_controller.attach_object_to_member(
            obj_name, puppet_name, member_name
        )

    def detach_object(self, obj_name: str) -> None:
        """Detach an object from any parent."""
        self.win.object_controller.detach_object(obj_name)

    def _create_object_from_file(
        self, file_path: str, scene_pos: Optional[QPointF] = None
    ) -> Optional[str]:
        """Create an object from a file."""
        return cast(
            Optional[str],
            self.win.object_controller.create_object_from_file(file_path, scene_pos),
        )

    def _add_object_graphics(self, obj: SceneObject) -> None:
        """Compatibility shim used by scene import to create graphics for an object.

        Delegates to ObjectOps' internal method until a public API is standardized.
        """
        try:
            self.win.object_view_adapter.add_object_graphics(obj)
        except Exception as e:  # pylint: disable=broad-except
            logging.error("add_object_graphics failed: %s", e)

    def delete_object_from_current_frame(self, name: str) -> None:
        """Delete an object from the current frame."""
        self.win.object_controller.delete_object_from_current_frame(name)

    def create_light_object(self) -> None:
        """Create a light object in the scene."""
        self.win.object_controller.create_light_object()

    # --- Library operations -----------------------------------------------
    def _add_library_item_to_scene(self, payload: LibraryPayload) -> None:
        """Add a library item to the scene."""
        self.library_ops.add_library_item_to_scene(payload)

    def handle_library_drop(self, payload: LibraryPayload, pos: QPointF) -> None:
        """Handle a library drop at the given position."""
        self.library_ops.handle_library_drop(payload, pos)

    # --- Visuals -----------------------------------------------------------
    def update_scene_visuals(self) -> None:
        """Update scene visuals."""
        self.view.update_scene_visuals()

    def update_background(self) -> None:
        """Update the scene background."""
        self.view.update_background()

    def set_background_path(self, path: Optional[str]) -> None:
        """Set the path for the scene background."""
        self.service.set_background_path(path)

    # --- View & zoom ------------------------------------------------------
    def zoom(self, factor: float) -> None:
        """Zoom the view by a factor."""
        self.view.zoom(factor)

    # --- Onion skin -------------------------------------------------------
    def set_onion_enabled(self, enabled: bool) -> None:
        """Enable or disable onion skinning."""
        self.onion.set_enabled(enabled)

    def clear_onion_skins(self) -> None:
        """Clear all onion skins."""
        self.onion.clear()

    def update_onion_skins(self) -> None:
        """Update onion skins."""
        self.onion.update()

    # --- State application -------------------------------------------------
    def apply_puppet_states(
        self,
        graphics_items: dict[str, QGraphicsItem],
        keyframes: dict[int, Keyframe],
        index: int,
    ) -> None:
        """Apply puppet states to graphics items."""
        self.applier.apply_puppet_states(graphics_items, keyframes, index)

    def apply_object_states(
        self,
        graphics_items: dict[str, QGraphicsItem],
        keyframes: dict[int, Keyframe],
        index: int,
    ) -> None:
        """Apply object states to graphics items."""
        self.applier.apply_object_states(graphics_items, keyframes, index)

    # --- Scene settings ---------------------------------------------------
    def set_scene_size(self, width: int, height: int) -> None:
        """Set the scene dimensions."""
        self.service.set_scene_size(width, height)
