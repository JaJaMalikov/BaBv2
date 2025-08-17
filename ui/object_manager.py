"""Module for managing objects in the scene."""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Dict, Optional, Any

from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene # Added QGraphicsScene

from core.scene_model import SceneModel
from core.puppet_piece import PuppetPiece

if TYPE_CHECKING:
    from ui.main_window import MainWindow


# pylint: disable=R0902
class ObjectManager:
    """Manages puppets and objects (creation, deletion, manipulation) in the scene."""
    def __init__(self, win: MainWindow) -> None:
        """Initialize the object manager.

        Args:
            win: The main window of the application.
        """
        self.win: MainWindow = win
        self.scene: QGraphicsScene = win.scene
        self.scene_model: SceneModel = win.scene_model
        self.graphics_items: Dict[str, QGraphicsItem] = {}
        self.renderers: Dict[str, Any] = {} # QSvgRenderer is not directly imported
        self.puppet_scales: Dict[str, float] = {}
        self.puppet_paths: Dict[str, str] = {}
        self.puppet_z_offsets: Dict[str, int] = {}

    def capture_puppet_states(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Capture the states of all puppets in the scene."""
        states: Dict[str, Dict[str, Dict[str, Any]]] = {}
        for name, puppet in self.scene_model.puppets.items():
            puppet_state: Dict[str, Dict[str, Any]] = {}
            for member_name in puppet.members:
                piece: Optional[PuppetPiece] = self.graphics_items.get(f"{name}:{member_name}")
                if piece:
                    puppet_state[member_name] = {
                        'rotation': piece.local_rotation,
                        'pos': (piece.x(), piece.y()),
                    }
            # If the puppet defines variant slots, snapshot which variant is visible
            if getattr(puppet, "variants", None):
                variants_state: Dict[str, Any] = {}
                for slot, candidates in puppet.variants.items():
                    active = None
                    for cand in candidates:
                        gi = self.graphics_items.get(f"{name}:{cand}")
                        try:
                            if gi and gi.isVisible():
                                active = cand
                                break
                        except RuntimeError:
                            continue
                    if active is None and candidates:
                        active = candidates[0]
                    if active is not None:
                        variants_state[slot] = active
                if variants_state:
                    puppet_state["_variants"] = variants_state
            states[name] = puppet_state
        return states

    # --- Snapshot helpers ---
    def capture_visible_object_states(self) -> Dict[str, Dict[str, Any]]:
        """Capture on-screen state for visible objects."""
        states: Dict[str, Dict[str, Any]] = {}
        # Build a reverse map from PuppetPiece to (puppet, member)
        piece_owner: Dict[QGraphicsItem, tuple[str, str]] = {}
        for key, val in self.graphics_items.items():
            if isinstance(val, PuppetPiece) and ":" in key:
                try:
                    puppet_name, member_name = key.split(":", 1)
                    piece_owner[val] = (puppet_name, member_name)
                except ValueError as e:
                    logging.debug("Split key '%s' failed: %s", key, e)
        for name, obj in self.scene_model.objects.items():
            gi: Optional[QGraphicsItem] = self.graphics_items.get(name)
            if gi and gi.isVisible():
                parent = gi.parentItem()
                attached_to = piece_owner.get(parent)
                data = obj.to_dict()
                try:
                    data["x"] = float(gi.x())
                    data["y"] = float(gi.y())
                    data["rotation"] = float(gi.rotation())
                    data["scale"] = float(gi.scale())
                    data["z"] = int(gi.zValue())
                except RuntimeError as e:
                    logging.debug("Reading graphics item state for '%s' failed: %s", name, e)
                data["attached_to"] = attached_to
                states[name] = data
        return states

    def capture_scene_state(self) -> Dict[str, Dict[str, Any]]:
        """Capture puppet and visible object states."""
        return {
            "puppets": self.capture_puppet_states(),
            "objects": self.capture_visible_object_states(),
        }

    def snapshot_current_frame(self) -> None:
        """Snapshot the current frame."""
        cur: int = self.scene_model.current_frame
        state = self.capture_scene_state()
        self.scene_model.add_keyframe(cur, state)
        # Ensure marker exists
        try:
            self.win.timeline_widget.add_keyframe_marker(cur)
        except RuntimeError as e:
            logging.debug("Failed to add keyframe marker at %s: %s", cur, e)
