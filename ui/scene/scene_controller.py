"""SceneController: façade légère regroupant les opérations de scène."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, Protocol, cast

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene

from core.scene_model import Keyframe, SceneModel
from .state_applier import StateApplier
from .scene_visuals import SceneVisuals
from ..onion_skin import OnionSkinManager
from .puppet_ops import PuppetOps
from .object_ops import ObjectOps
from .library_ops import LibraryOps, LibraryPayload

if TYPE_CHECKING:
    from ..object_manager import ObjectManager
    from ..zoomable_view import ZoomableView


class InspectorWidgetProtocol(Protocol):
    """Protocol describing the interface expected from the inspector widget."""

    def refresh(self) -> None:
        """Refresh the inspector's displayed information."""


class MainWindowProtocol(Protocol):
    """Minimal protocol for the main window used by scene operations."""

    scene: QGraphicsScene
    scene_model: SceneModel
    object_manager: ObjectManager
    view: ZoomableView
    zoom_factor: float
    _suspend_item_updates: bool
    inspector_widget: InspectorWidgetProtocol

    def add_keyframe(self, index: int) -> None:
        """Insert a keyframe at the given timeline index."""

    def _update_background(self) -> None: ...

    def _update_zoom_status(self) -> None: ...


class SceneController:
    """Facade orchestrating scene-related operations."""

    def __init__(
        self,
        win: MainWindowProtocol,
        *,
        visuals: SceneVisuals | None = None,
        onion: OnionSkinManager | None = None,
        applier: StateApplier | None = None,
    ) -> None:
        """Initialize the scene controller."""
        self.win = win
        self.visuals: SceneVisuals = visuals if visuals is not None else SceneVisuals(win)
        if visuals is None:
            self.visuals.setup()
        self.onion: OnionSkinManager = onion if onion is not None else OnionSkinManager(win)
        self.applier: StateApplier = applier if applier is not None else StateApplier(win)
        self.puppet_ops = PuppetOps(win)
        self.object_ops = ObjectOps(win)
        self.library_ops = LibraryOps(win, self.puppet_ops, self.object_ops, self.set_background_path)

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

    # --- Object operations -------------------------------------------------
    def delete_object(self, name: str) -> None:
        """Delete an object."""
        self.object_ops.delete_object(name)

    def duplicate_object(self, name: str) -> None:
        """Duplicate an object."""
        self.object_ops.duplicate_object(name)

    def attach_object_to_member(self, obj_name: str, puppet_name: str, member_name: str) -> None:
        """Attach an object to a puppet member."""
        self.object_ops.attach_object_to_member(obj_name, puppet_name, member_name)

    def detach_object(self, obj_name: str) -> None:
        """Detach an object from any parent."""
        self.object_ops.detach_object(obj_name)

    def _create_object_from_file(self, file_path: str, scene_pos: Optional[QPointF] = None) -> Optional[str]:
        """Create an object from a file."""
        return cast(Optional[str], self.object_ops.create_object_from_file(file_path, scene_pos))

    def delete_object_from_current_frame(self, name: str) -> None:
        """Delete an object from the current frame."""
        self.object_ops.delete_object_from_current_frame(name)

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
        self.visuals.update_scene_visuals()

    def update_background(self) -> None:
        """Update the scene background."""
        self.visuals.update_background()

    def set_background_path(self, path: Optional[str]) -> None:
        """Set the path for the scene background."""
        self.win.scene_model.background_path = path
        self.update_background()

    # --- View & zoom ------------------------------------------------------
    def zoom(self, factor: float) -> None:
        """Zoom the view by a factor."""
        self.win.view.scale(factor, factor)
        self.win.zoom_factor *= factor
        try:
            self.win._update_zoom_status()
        except (RuntimeError, AttributeError):
            logging.exception("Failed to update zoom status")

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
        self.win.scene_model.scene_width = int(width)
        self.win.scene_model.scene_height = int(height)
        self.win.scene.setSceneRect(0, 0, int(width), int(height))
        self.update_scene_visuals()
        self.update_background()
        try:
            self.win._update_zoom_status()
        except (RuntimeError, AttributeError):
            logging.exception("Failed to update zoom status after scene resize")
