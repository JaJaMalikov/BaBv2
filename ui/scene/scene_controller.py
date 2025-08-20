"""SceneController: façade légère regroupant les opérations de scène.

Data flow overview (see ARCHITECTURE.md §Sequence diagrams):
- UI (widgets/adapters) → calls controller methods or emits signals
- Controller → delegates model mutations to SceneService (Qt‑agnostic API)
- Service → updates SceneModel and emits signals about changes
- Controller/View adapters → apply state to QGraphicsItems and refresh visuals

This controller keeps UI code thin by delegating business logic to services and
state application to adapters, preserving testability.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional, Protocol, cast

# Controller boundaries: keep Qt usage minimal; avoid passing Qt graphics types across service boundaries
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene

from core.scene_model import Keyframe, SceneModel, SceneObject
from controllers.scene_service import SceneService
from .state_applier import StateApplier
from .scene_view import SceneView
from ..onion_skin import OnionSkinManager
from .puppet_ops import PuppetOps
from .library_ops import LibraryOps, LibraryPayload
from ..utils import show_error_dialog
from core.logging_config import log_with_context

if TYPE_CHECKING:
    from ..object_view_adapter import ObjectViewAdapter
    from ..zoomable_view import ZoomableView
    from controllers.object_controller import ObjectController


class InspectorWidgetProtocol(Protocol):
    """Protocol describing the interface expected from the inspector widget."""

    def refresh(self) -> None:
        """Refresh the inspector's displayed information."""


class MainWindowProtocol(Protocol):
    """Minimal protocol for the main window used by scene operations."""

    scene: QGraphicsScene
    scene_model: SceneModel
    object_manager: ObjectViewAdapter
    object_view_adapter: ObjectViewAdapter
    object_controller: "ObjectController"
    view: ZoomableView
    zoom_factor: float
    _suspend_item_updates: bool
    inspector_widget: InspectorWidgetProtocol

    controller: Any

    def _update_background(self) -> None: ...

    def _update_zoom_status(self) -> None: ...


class SceneController:
    """Facade orchestrating scene-related operations.

    Bridges UI and the Qt-agnostic SceneService; see the module docstring for
    the end-to-end data flow and ARCHITECTURE.md for sequence diagrams.
    """

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
        self.service = (
            service
            if service is not None
            else SceneService(win.scene_model, win.object_controller.capture_scene_state)
        )
        self.view = view if view is not None else SceneView(win)
        self.onion: OnionSkinManager = onion if onion is not None else OnionSkinManager(win)
        self.applier: StateApplier = applier if applier is not None else StateApplier(win)
        self.puppet_ops = PuppetOps(win, self.service)
        self.library_ops = LibraryOps(win, self.puppet_ops, win.object_controller, self.service)
        self.service.background_changed.connect(self.view.update_background)
        self.service.scene_resized.connect(self.view.handle_scene_resized)
        # Bridge domain model change events to UI refresh notifications
        try:
            from ui.selection_sync import emit_model_changed as _emit_model_changed

            self.service.model_changed.connect(lambda: _emit_model_changed(self.win))
        except Exception:
            # Keep resilient if selection_sync is not available in some tests
            pass

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

    def get_puppet_scale(self, puppet_name: str) -> float:
        """Return the current stored absolute scale of a puppet (default 1.0)."""
        try:
            return float(getattr(self.win, "object_manager").puppet_scales.get(puppet_name, 1.0))
        except Exception:
            return 1.0

    def set_puppet_scale(self, puppet_name: str, value: float) -> None:
        """Set absolute puppet scale and apply ratio via PuppetOps.

        Centralizes scale handling to avoid direct UI writes to adapter state.
        No-op if value <= 0.
        """
        try:
            if value <= 0:
                return
            old = self.get_puppet_scale(puppet_name)
            ratio = (value / old) if old else value
            getattr(self.win, "object_manager").puppet_scales[puppet_name] = float(value)
            self.scale_puppet(puppet_name, float(ratio))
        except Exception:
            # Keep resilient; scaling is best-effort
            pass

    def get_puppet_z_offset(self, puppet_name: str) -> int:
        """Return the current Z offset for a puppet (default 0)."""
        try:
            return int(getattr(self.win, "object_manager").puppet_z_offsets.get(puppet_name, 0))
        except Exception:
            return 0

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
    def set_member_variant(self, puppet_name: str, slot: str, variant_name: str) -> None:
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
        try:
            self.win.inspector_widget.refresh()
        except AttributeError:
            pass

    def duplicate_object(self, name: str) -> None:
        """Duplicate an object."""
        self.win.object_controller.duplicate_object(name)
        try:
            self.win.inspector_widget.refresh()
        except AttributeError:
            pass

    def attach_object_to_member(self, obj_name: str, puppet_name: str, member_name: str) -> None:
        """Attach an object to a puppet member."""
        self.win.object_controller.attach_object_to_member(obj_name, puppet_name, member_name)
        try:
            self.win.inspector_widget.refresh()
        except AttributeError:
            pass

    def detach_object(self, obj_name: str) -> None:
        """Detach an object from any parent."""
        self.win.object_controller.detach_object(obj_name)
        try:
            self.win.inspector_widget.refresh()
        except AttributeError:
            pass

    def _create_object_from_file(
        self, file_path: str, scene_pos: Optional[QPointF] = None
    ) -> Optional[str]:
        """Create an object from a file."""
        name = cast(
            Optional[str],
            self.win.object_controller.create_object_from_file(file_path, scene_pos),
        )
        try:
            self.win.inspector_widget.refresh()
        except AttributeError:
            pass
        return name

    def _add_object_graphics(self, obj: SceneObject) -> None:
        """Compatibility shim used by scene import to create graphics for an object.

        Delegates to ObjectOps' internal method until a public API is standardized.
        """
        try:
            self.win.object_view_adapter.add_object_graphics(obj)
        except (RuntimeError, AttributeError, TypeError) as e:
            log_with_context(
                logging.getLogger(__name__),
                logging.ERROR,
                "add_object_graphics failed",
                op="add_object_graphics",
                object=obj.name,
                error=str(e),
            )
            show_error_dialog(
                getattr(self.win, "view", None),
                "Erreur d'ajout",
                f"Impossible d'ajouter l'objet '{obj.name}'. Consultez les logs pour plus de détails.",
            )

    def delete_object_from_current_frame(self, name: str) -> None:
        """Delete an object from the current frame."""
        self.win.object_controller.delete_object_from_current_frame(name)
        try:
            self.win.inspector_widget.refresh()
        except AttributeError:
            pass

    def create_light_object(self) -> None:
        """Create a light object in the scene."""
        self.win.object_controller.create_light_object()
        try:
            self.win.inspector_widget.refresh()
        except AttributeError:
            pass

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

    def apply_onion_settings_from_qsettings(self, qsettings: Any) -> None:  # type: ignore[no-untyped-def]
        """Apply onion-related options from QSettings into the OnionSkinManager.

        Uses SettingsService.key to resolve namespaced keys so the logic stays
        controller-bound and testable. UI should delegate here instead of
        mutating OnionSkinManager fields directly (docs/tasks.md §17).
        """
        try:
            from controllers.settings_service import SettingsService as _SS

            self.onion.prev_count = int(
                qsettings.value(_SS.key("onion", "prev_count"), self.onion.prev_count)
            )
            self.onion.next_count = int(
                qsettings.value(_SS.key("onion", "next_count"), self.onion.next_count)
            )
            self.onion.opacity_prev = float(
                qsettings.value(_SS.key("onion", "opacity_prev"), self.onion.opacity_prev)
            )
            self.onion.opacity_next = float(
                qsettings.value(_SS.key("onion", "opacity_next"), self.onion.opacity_next)
            )
            # Performance toggles
            try:
                self.onion.pixmap_mode = bool(
                    qsettings.value(_SS.key("onion", "pixmap_mode"), self.onion.pixmap_mode)
                )
                self.onion.pixmap_scale = float(
                    qsettings.value(_SS.key("onion", "pixmap_scale"), self.onion.pixmap_scale)
                )
            except Exception:
                pass
        except Exception:
            logging.debug("apply_onion_settings_from_qsettings failed", exc_info=True)

    def apply_onion_settings_from_schema(self, schema: Any) -> None:
        """Apply onion-related options from a SettingsSchema instance.

        Only reads fields used by onion; safe to be called with any object
        that has the attributes used below. This keeps the controller independent
        from importing the dataclass in common UI paths.
        """
        try:
            span = max(0, int(getattr(schema, "onion_span", getattr(schema, "span", 0))))
            op = float(getattr(schema, "onion_opacity", getattr(schema, "opacity", 0.25)))
            self.onion.prev_count = span
            self.onion.next_count = span
            self.onion.opacity_prev = op
            self.onion.opacity_next = op
            # Performance toggles from schema if available
            if hasattr(schema, "onion_pixmap_mode"):
                self.onion.pixmap_mode = bool(getattr(schema, "onion_pixmap_mode"))
            if hasattr(schema, "onion_pixmap_scale"):
                try:
                    scale = float(getattr(schema, "onion_pixmap_scale"))
                    self.onion.pixmap_scale = max(0.1, min(1.0, scale))
                except Exception:
                    pass
            # If onion is enabled, refresh to apply changes
            if getattr(self.onion, "enabled", False):
                self.onion.update()
        except Exception:
            logging.debug("apply_onion_settings_from_schema failed", exc_info=True)

    # --- State application -------------------------------------------------
    def apply_puppet_states(
        self,
        graphics_items: dict[str, Any],
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

    def get_scene_size(self) -> tuple[int, int]:
        """Return the scene dimensions (width, height) from the service."""
        return self.service.get_scene_size()
