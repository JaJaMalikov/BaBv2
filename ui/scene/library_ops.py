"""Helpers for loading assets from the library into the scene.

DEPRECATION NOTICE (docs/tasks.md §23):
- Direct calls to `win.inspector_widget.refresh()` and direct graphics access are
  temporary. Replace with event emission and facade queries in upcoming refactors.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional, TypedDict, Any

from core.types import Kind

from PySide6.QtCore import QPointF

if TYPE_CHECKING:
    from .scene_controller import MainWindowProtocol
    from .puppet_ops import PuppetOps
    from controllers.object_controller import ObjectController
    from controllers.scene_service import SceneService
    from ui.protocols import MessageAdapterProtocol


class LibraryPayload(TypedDict, total=False):
    """Data describing an asset selected from the library.

    Note: ``kind`` is serialized as a lowercase string in drag-n-drop payloads
    but maps to core.types.Kind values. """

    kind: str
    path: str


class LibraryOps:
    """Operations for interacting with the asset library."""

    def __init__(
        self,
        win: MainWindowProtocol,
        puppet_ops: PuppetOps,
        object_ctrl: ObjectController,
        scene_service: SceneService,
        message_adapter: Any | None = None,
    ) -> None:
        """Initialize helpers to route library items into the scene."""
        self.win = win
        self.puppets = puppet_ops
        self.objects = object_ctrl
        self.scene_service = scene_service
        # Optional UI message adapter to surface errors to users (docs/tasks.md §18)
        self._msg = message_adapter

    def add_library_item_to_scene(self, payload: LibraryPayload) -> None:
        """Adds a library item to the scene."""
        self._add_library_payload(payload, scene_pos=None)

    def handle_library_drop(self, payload: LibraryPayload, pos: QPointF) -> None:
        """Handles a library item drop event."""
        scene_pt: QPointF = self.win.view.mapToScene(pos.toPoint())
        self._add_library_payload(payload, scene_pos=scene_pt)

    def _add_library_payload(self, payload: LibraryPayload, scene_pos: QPointF | None) -> None:
        """Internal helper adding a payload to the scene."""
        kind_str: Optional[str] = payload.get("kind")
        path: Optional[str] = payload.get("path")
        if not kind_str or not path:
            return

        kind = Kind.from_str(kind_str)
        if kind is Kind.BACKGROUND:
            self.scene_service.set_background_path(path)
        elif kind is Kind.OBJECT:
            self.objects.create_object_from_file(path, scene_pos)
            # Emit a model-changed event so interested UI (e.g., Inspector) can refresh
            from ui.selection_sync import emit_model_changed

            emit_model_changed(self.win)
        elif kind is Kind.PUPPET:
            base: str = Path(path).stem
            name: str = self.puppets.unique_puppet_name(base)
            self.puppets.add_puppet(path, name)
            if scene_pos is not None:
                try:
                    # Delegate root positioning to PuppetOps to avoid direct graphics access
                    self.puppets.set_puppet_root_pos(name, scene_pos)
                except Exception as e:  # pylint: disable=broad-except
                    logging.error(f"Positioning puppet failed: {e}")
                    if self._msg is not None:
                        try:
                            # type: ignore[attr-defined]
                            self._msg.show_message("Impossible de positionner le pantin.", "warning")
                        except Exception:
                            pass
        else:
            logging.error(f"Unknown library kind: {kind_str}")
            if self._msg is not None:
                try:
                    # type: ignore[attr-defined]
                    self._msg.show_message(f"Type d'élément inconnu: {kind_str}", "error")
                except Exception:
                    pass
