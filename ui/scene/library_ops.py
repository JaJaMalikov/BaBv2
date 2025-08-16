"""Helpers for loading assets from the library into the scene."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional, TypedDict

from PySide6.QtCore import QPointF

if TYPE_CHECKING:
    from .scene_controller import MainWindowProtocol
    from .puppet_ops import PuppetOps
    from .object_ops import ObjectOps
    from typing import Callable


class LibraryPayload(TypedDict, total=False):
    """Data describing an asset selected from the library."""

    kind: str
    path: str


class LibraryOps:
    """Operations for interacting with the asset library."""

    def __init__(
        self,
        win: MainWindowProtocol,
        puppet_ops: PuppetOps,
        object_ops: ObjectOps,
        set_background_path: "Callable[[Optional[str]], None]",
    ) -> None:
        """Initialize helpers to route library items into the scene."""
        self.win = win
        self.puppets = puppet_ops
        self.objects = object_ops
        self.set_background_path = set_background_path

    def add_library_item_to_scene(self, payload: LibraryPayload) -> None:
        """Adds a library item to the scene."""
        self._add_library_payload(payload, scene_pos=None)

    def handle_library_drop(self, payload: LibraryPayload, pos: QPointF) -> None:
        """Handles a library item drop event."""
        scene_pt: QPointF = self.win.view.mapToScene(pos.toPoint())
        self._add_library_payload(payload, scene_pos=scene_pt)

    def _add_library_payload(
        self, payload: LibraryPayload, scene_pos: QPointF | None
    ) -> None:
        """Internal helper adding a payload to the scene."""
        kind: Optional[str] = payload.get("kind")
        path: Optional[str] = payload.get("path")
        if not kind or not path:
            return

        if kind == "background":
            try:
                self.set_background_path(path)
            except (OSError, RuntimeError):
                logging.exception("Failed to set background path")
                self.win.scene_model.background_path = path
                self.win._update_background()
        elif kind == "object":
            self.objects.create_object_from_file(path, scene_pos)
        elif kind == "puppet":
            base: str = Path(path).stem
            name: str = self.puppets.unique_puppet_name(base)
            self.puppets.add_puppet(path, name)
            if scene_pos is not None:
                try:
                    root_member_name: str = (
                        self.win.scene_model.puppets[name].get_root_members()[0].name
                    )
                    root_piece = self.win.object_manager.graphics_items.get(
                        f"{name}:{root_member_name}"
                    )
                    if root_piece:
                        root_piece.setPos(scene_pos.x(), scene_pos.y())
                except (KeyError, AttributeError, RuntimeError) as e:
                    logging.error(f"Positioning puppet failed: {e}")
        else:
            logging.error(f"Unknown library kind: {kind}")
