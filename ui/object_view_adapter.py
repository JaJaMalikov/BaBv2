from __future__ import annotations

"""Adaptateur manipulant les ``QGraphicsItem`` des objets et pantins."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Optional, Any

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene

from core.scene_model import SceneModel, SceneObject
from core.puppet_piece import PuppetPiece
from core.naming import unique_name
from .object_item import (
    ObjectPixmapItem,
    ObjectSvgItem,
    LightItem,
    DEFAULT_LIGHT_COLOR,
    DEFAULT_LIGHT_CONE_ANGLE,
    DEFAULT_LIGHT_CONE_REACH,
)

if TYPE_CHECKING:  # pragma: no cover - hints only
    from ui.main_window import MainWindow


# pylint: disable=R0902
class ObjectViewAdapter:
    """Gère la partie graphique (Qt) des objets et pantins.

    This adapter encapsulates all QGraphics-based manipulations for objects and
    puppets, keeping controllers/services Qt-agnostic. It exposes helpers to
    capture current states and to build/remove graphics items corresponding to
    model objects.
    """

    def __init__(self, win: MainWindow) -> None:
        """Initialize the adapter with the MainWindow dependencies."""
        self.win = win
        self.scene: QGraphicsScene = win.scene
        self.scene_model: SceneModel = win.scene_model
        self.graphics_items: Dict[str, QGraphicsItem] = {}
        self.renderers: Dict[str, Any] = {}
        self.puppet_scales: Dict[str, float] = {}
        self.puppet_paths: Dict[str, str] = {}
        self.puppet_z_offsets: Dict[str, int] = {}

    # ------------------------------------------------------------------
    # Capture d'état
    def capture_puppet_states(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Return the state of all puppet members and active variants.

        Output structure per puppet name:
        {
            member_name: {"rotation": float, "pos": (x: float, y: float)},
            "_variants": {slot: active_variant}
        }
        """
        states: Dict[str, Dict[str, Dict[str, Any]]] = {}
        for name, puppet in self.scene_model.puppets.items():
            puppet_state: Dict[str, Dict[str, Any]] = {}
            for member_name in puppet.members:
                piece: Optional[PuppetPiece] = self.graphics_items.get(
                    f"{name}:{member_name}"
                )
                if piece:
                    puppet_state[member_name] = {
                        "rotation": piece.local_rotation,
                        "pos": (piece.x(), piece.y()),
                    }
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

    def capture_visible_object_states(self) -> Dict[str, Dict[str, Any]]:
        """Return states for all currently visible objects.

        Each entry contains fields from the model plus live graphics values
        (x, y, rotation, scale, z) and an "attached_to" tuple if the object is
        parented to a puppet member.
        """
        states: Dict[str, Dict[str, Any]] = {}
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
                    logging.debug(
                        "Reading graphics item state for '%s' failed: %s", name, e
                    )
                data["attached_to"] = attached_to
                states[name] = data
        return states

    def read_item_state(self, name: str) -> Dict[str, Any]:
        """Return the effective state for a given object name."""
        obj = self.scene_model.objects.get(name)
        if not obj:
            return {}
        states = self.capture_visible_object_states()
        return states.get(name, obj.to_dict())

    # ------------------------------------------------------------------
    # Gestion des items
    def add_object_graphics(self, obj: SceneObject) -> None:
        """Create and add the appropriate QGraphicsItem for the object."""
        item: QGraphicsItem
        if obj.obj_type == "image":
            item = ObjectPixmapItem(obj.file_path)
        elif obj.obj_type == "light":
            item = LightItem(
                color_str=obj.color or DEFAULT_LIGHT_COLOR,
                angle=obj.cone_angle or DEFAULT_LIGHT_CONE_ANGLE,
                reach=obj.cone_reach or DEFAULT_LIGHT_CONE_REACH,
            )
        else:
            item = ObjectSvgItem(obj.file_path)
        item.set_context(self.win, obj.name)
        self.win._suspend_item_updates = True
        try:
            item.setPos(obj.x, obj.y)
            item.setRotation(obj.rotation)
            item.setScale(obj.scale)
        finally:
            self.win._suspend_item_updates = False
        if not item.boundingRect().isEmpty():
            item.setTransformOriginPoint(item.boundingRect().center())
        else:
            logging.warning(
                "Cannot set transform origin point for %s: bounding rect is empty.",
                obj.name,
            )
        try:
            item.setZValue(getattr(obj, "z", 0))
        except RuntimeError as e:
            logging.error("Error setting Z-value for %s: %s", obj.name, e)
        item.setFlag(QGraphicsItem.ItemIsMovable, True)
        item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.scene.addItem(item)
        self.graphics_items[obj.name] = item

    def remove_object_graphics(self, name: str) -> None:
        """Remove the QGraphicsItem associated with the given object name."""
        if item := self.graphics_items.pop(name, None):
            self.scene.removeItem(item)

    def hide_object(self, name: str) -> None:
        """Hide the graphics item for the given object name (if present)."""
        if item := self.graphics_items.get(name):
            item.setVisible(False)

    # ------------------------------------------------------------------
    # Création d'objets
    def create_object_from_file(
        self, file_path: str, scene_pos: Optional[QPointF] = None
    ) -> Optional[tuple[SceneObject, Dict[str, Any]]]:
        """Create an object from a file path and add it to the scene.

        Returns a tuple (SceneObject, state_dict) on success, or None on error.
        If scene_pos is None, centers the object in the scene.
        """
        ext: str = Path(file_path).suffix.lower()
        if ext in (".png", ".jpg", ".jpeg"):
            obj_type = "image"
        elif ext == ".svg":
            obj_type = "svg"
        else:
            logging.error("Unsupported object file type: %s", ext)
            return None
        base: str = Path(file_path).stem
        name: str = self._unique_object_name(base)
        if scene_pos is None:
            c: QPointF = self.scene.sceneRect().center()
            x, y = c.x(), c.y()
        else:
            x, y = float(scene_pos.x()), float(scene_pos.y())
        obj = SceneObject(name, obj_type, file_path, x=x, y=y, rotation=0, scale=1.0, z=0)
        self.add_object_graphics(obj)
        state = self.read_item_state(obj.name)
        return obj, state

    def create_light_object(
        self, scene_pos: Optional[QPointF] = None
    ) -> Optional[tuple[SceneObject, Dict[str, Any]]]:
        base = "projecteur"
        name = self._unique_object_name(base)
        if scene_pos is None:
            c: QPointF = self.scene.sceneRect().center()
            x, y = c.x(), c.y() - 200
        else:
            x, y = float(scene_pos.x()), float(scene_pos.y())
        obj = SceneObject(
            name,
            obj_type="light",
            file_path="",
            x=x,
            y=y,
            rotation=0,
            scale=1.0,
            z=100,
            color="#FFFFE0",
            cone_angle=45.0,
            cone_reach=500.0,
        )
        self.add_object_graphics(obj)
        state = self.read_item_state(obj.name)
        return obj, state

    def _unique_object_name(self, base: str) -> str:
        existing = set(self.scene_model.objects.keys()) | set(self.graphics_items.keys())
        return unique_name(base, existing)

    # ------------------------------------------------------------------
    # Attachements
    def attach_object_to_member(
        self, obj_name: str, puppet_name: str, member_name: str
    ) -> Dict[str, Any]:
        obj = self.scene_model.objects.get(obj_name)
        item = self.graphics_items.get(obj_name)
        parent_piece = self.graphics_items.get(f"{puppet_name}:{member_name}")
        if not obj or not item or not isinstance(parent_piece, PuppetPiece):
            return {}
        from math import atan2, degrees, sqrt

        wt = item.sceneTransform()
        m11, m12, m21, m22 = (
            float(wt.m11()),
            float(wt.m12()),
            float(wt.m21()),
            float(wt.m22()),
        )
        world_rot = degrees(atan2(m12, m11))
        world_sx = sqrt(m11 * m11 + m21 * m21)
        world_sy = sqrt(m12 * m12 + m22 * m22) if (m12 or m22) else world_sx
        scene_pt: QPointF = item.mapToScene(item.transformOriginPoint())

        pt = parent_piece.sceneTransform()
        pm11, pm12, pm21, pm22 = (
            float(pt.m11()),
            float(pt.m12()),
            float(pt.m21()),
            float(pt.m22()),
        )
        parent_rot = degrees(atan2(pm12, pm11))
        parent_sx = sqrt(pm11 * pm11 + pm21 * pm21)
        parent_sy = sqrt(pm12 * pm12 + pm22 * pm22) if (pm12 or pm22) else parent_sx

        self.win._suspend_item_updates = True
        try:
            item.setParentItem(parent_piece)
            try:
                item.setRotation(world_rot - parent_rot)
                lx = world_sx / (parent_sx if parent_sx != 0 else 1.0)
                ly = world_sy / (parent_sy if parent_sy != 0 else 1.0)
                lscale = (lx + ly) * 0.5 if ly > 0 else lx
                item.setScale(lscale)
            except (RuntimeError, ZeroDivisionError, AttributeError):
                logging.exception("Failed to adjust item transform during attach")
            local_pt: QPointF = parent_piece.mapFromScene(scene_pt)
            item.setPos(local_pt - item.transformOriginPoint())
        finally:
            self.win._suspend_item_updates = False
        return self.read_item_state(obj_name)

    def detach_object(self, obj_name: str) -> Dict[str, Any]:
        obj = self.scene_model.objects.get(obj_name)
        item = self.graphics_items.get(obj_name)
        if not obj or not item:
            return {}
        from math import atan2, degrees, sqrt

        wt = item.sceneTransform()
        m11, m12, m21, m22 = (
            float(wt.m11()),
            float(wt.m12()),
            float(wt.m21()),
            float(wt.m22()),
        )
        world_rot = degrees(atan2(m12, m11))
        world_sx = sqrt(m11 * m11 + m21 * m21)
        world_sy = sqrt(m12 * m12 + m22 * m22) if (m12 or m22) else world_sx
        scene_pt: QPointF = item.mapToScene(item.transformOriginPoint())
        parent_z = item.parentItem().zValue() if item.parentItem() is not None else 0.0

        self.win._suspend_item_updates = True
        try:
            item.setParentItem(None)
            try:
                lscale = (world_sx + world_sy) * 0.5
                item.setScale(lscale)
                item.setRotation(world_rot)
            except (RuntimeError, AttributeError):
                logging.exception("Failed to adjust transform during detach")
            try:
                item.setZValue(float(item.zValue()) + float(parent_z))
            except (RuntimeError, TypeError, ValueError):
                logging.exception("Failed to adjust Z during detach")
            item.setPos(scene_pt - item.transformOriginPoint())
        finally:
            self.win._suspend_item_updates = False
        return self.read_item_state(obj_name)
