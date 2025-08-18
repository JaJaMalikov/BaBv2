"""Operations for creating, deleting, and managing scene objects.

This module provides utilities for creating, duplicating, attaching and
detaching objects within the scene and from puppet members.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsItem

from core.scene_model import Keyframe, SceneObject
from core.puppet_piece import PuppetPiece
from ..object_item import ObjectPixmapItem, ObjectSvgItem, LightItem

if TYPE_CHECKING:
    from .scene_controller import MainWindowProtocol


class ObjectOps:
    """
    A class to handle operations related to generic scene objects.

    Args:
        win: The main window instance.
    """

    def __init__(self, win: MainWindowProtocol) -> None:
        """
        Initializes the ObjectOps class.

        Args:
            win: The main window instance.
        """
        self.win = win

    def delete_object(self, name: str) -> None:
        """
        Deletes an object from the scene by removing its graphical representation and
        its data from the scene model.

        Args:
            name: The name of the object to delete.
        """
        if item := self.win.object_manager.graphics_items.pop(name, None):
            self.win.scene.removeItem(item)
        self.win.scene_model.remove_object(name)

    def duplicate_object(self, name: str) -> None:
        """
        Duplicates an object, giving it a unique name and adding it to the scene.

        Args:
            name: The name of the object to duplicate.
        """
        obj: Optional[SceneObject] = self.win.scene_model.objects.get(name)
        if not obj:
            return
        base: str = name
        i: int = 1
        new_name: str = f"{base}_{i}"
        while new_name in self.win.scene_model.objects:
            i += 1
            new_name = f"{base}_{i}"
        new_obj: SceneObject = SceneObject(
            new_name,
            obj.obj_type,
            obj.file_path,
            x=obj.x + 10,
            y=obj.y + 10,
            rotation=obj.rotation,
            scale=obj.scale,
            z=getattr(obj, "z", 0),
        )
        self.win.scene_model.add_object(new_obj)
        self._add_object_graphics(new_obj)

    def _add_object_graphics(self, obj: SceneObject) -> None:
        """
        Adds the graphical representation of a scene object to the scene.

        Args:
            obj: The scene object to add.
        """
        item: QGraphicsItem
        if obj.obj_type == "image":
            item = ObjectPixmapItem(obj.file_path)
        elif obj.obj_type == "light":
            item = LightItem(
                color_str=obj.color or "#FFFFE0",
                angle=obj.cone_angle or 45.0,
                reach=obj.cone_reach or 500.0,
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
                f"Cannot set transform origin point for {obj.name}: bounding rect is empty."
            )
        try:
            item.setZValue(getattr(obj, "z", 0))
        except RuntimeError as e:
            logging.error(f"Error setting Z-value for {obj.name}: {e}")
        item.setFlag(QGraphicsItem.ItemIsMovable, True)
        item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.win.scene.addItem(item)
        self.win.object_manager.graphics_items[obj.name] = item

    def attach_object_to_member(
        self, obj_name: str, puppet_name: str, member_name: str
    ) -> None:
        """
        Attaches a scene object to a puppet member, making it a child of the member.

        Args:
            obj_name: The name of the object to attach.
            puppet_name: The name of the puppet.
            member_name: The name of the puppet member to attach to.
        """
        obj: Optional[SceneObject] = self.win.scene_model.objects.get(obj_name)
        item: Optional[QGraphicsItem] = self.win.object_manager.graphics_items.get(
            obj_name
        )
        parent_piece: Optional[PuppetPiece] = (
            self.win.object_manager.graphics_items.get(f"{puppet_name}:{member_name}")
        )
        if not obj or not item or not parent_piece:
            return
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
        obj.attach(puppet_name, member_name)
        try:
            obj.x = float(item.x())
            obj.y = float(item.y())
            obj.rotation = float(item.rotation())
            obj.scale = float(item.scale())
            obj.z = int(item.zValue())
        except RuntimeError as e:
            logging.debug(
                "Failed to read item transform on attach for '%s': %s", obj_name, e
            )
        cur_idx = self.win.scene_model.current_frame
        if cur_idx not in self.win.scene_model.keyframes:
            self.win.controller.add_keyframe(cur_idx)
        kf: Optional[Keyframe] = self.win.scene_model.keyframes.get(cur_idx)
        if kf is not None:
            kf.objects[obj_name] = obj.to_dict()

    def detach_object(self, obj_name: str) -> None:
        """
        Detaches an object from its parent, making it a top-level item in the scene.

        Args:
            obj_name: The name of the object to detach.
        """
        obj: Optional[SceneObject] = self.win.scene_model.objects.get(obj_name)
        item: Optional[QGraphicsItem] = self.win.object_manager.graphics_items.get(
            obj_name
        )
        if not obj or not item:
            return
        prev_attachment = getattr(obj, "attached_to", None)
        if prev_attachment is not None:
            try:
                local_x, local_y = float(item.x()), float(item.y())
                cur_idx: int = self.win.scene_model.current_frame
                for idx, kf in list(self.win.scene_model.keyframes.items()):
                    if idx <= cur_idx and obj_name in kf.objects:
                        st = kf.objects[obj_name]
                        if (
                            st.get("attached_to") == list(prev_attachment)
                            or st.get("attached_to") == tuple(prev_attachment)
                            or st.get("attached_to") == prev_attachment
                        ):
                            sx = st.get("x", 0.0)
                            sy = st.get("y", 0.0)
                            try:
                                sx = float(sx)
                                sy = float(sy)
                            except (TypeError, ValueError):
                                sx, sy = 0.0, 0.0
                            if abs(sx) < 1e-9 and abs(sy) < 1e-9:
                                st["x"] = local_x
                                st["y"] = local_y
                                kf.objects[obj_name] = st
            except (KeyError, TypeError, ValueError) as e:
                logging.debug(
                    "While patching legacy keyframes for '%s': %s", obj_name, e
                )
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
        obj.detach()
        try:
            obj.x = float(item.x())
            obj.y = float(item.y())
            obj.rotation = float(item.rotation())
            obj.scale = float(item.scale())
            obj.z = int(item.zValue())
        except RuntimeError as e:
            logging.debug(
                "Failed to read item transform on detach for '%s': %s", obj_name, e
            )
        cur_idx = self.win.scene_model.current_frame
        if cur_idx not in self.win.scene_model.keyframes:
            self.win.controller.add_keyframe(cur_idx)
        kf: Optional[Keyframe] = self.win.scene_model.keyframes.get(cur_idx)
        if kf is not None:
            kf.objects[obj_name] = obj.to_dict()

    def unique_object_name(self, base: str) -> str:
        """
        Generates a unique name for an object by appending a number if the base name is taken.

        Args:
            base: The base name for the object.

        Returns:
            A unique name for the object.
        """
        name: str = base
        i: int = 1
        while name in self.win.scene_model.objects:
            name = f"{base}_{i}"
            i += 1
        return name

    def create_object_from_file(
        self, file_path: str, scene_pos: Optional[QPointF] = None
    ) -> Optional[str]:
        """
        Creates a scene object from a file and adds it to the scene.

        Args:
            file_path: The path to the file to create the object from.
            scene_pos: The position in the scene to create the object at.

        Returns:
            The name of the created object, or None if the file type is not supported.
        """
        ext: str = Path(file_path).suffix.lower()
        if ext in (".png", ".jpg", ".jpeg"):
            obj_type = "image"
        elif ext == ".svg":
            obj_type = "svg"
        else:
            logging.error(f"Unsupported object file type: {ext}")
            return None
        base: str = Path(file_path).stem
        name: str = self.unique_object_name(base)
        if scene_pos is None:
            c: QPointF = self.win.scene.sceneRect().center()
            x, y = c.x(), c.y()
        else:
            x, y = float(scene_pos.x()), float(scene_pos.y())
        obj: SceneObject = SceneObject(
            name, obj_type, file_path, x=x, y=y, rotation=0, scale=1.0, z=0
        )
        self.win.scene_model.add_object(obj)
        self._add_object_graphics(obj)
        cur: int = self.win.scene_model.current_frame
        if cur not in self.win.scene_model.keyframes:
            self.win.controller.add_keyframe(cur)
        kf: Optional[Keyframe] = self.win.scene_model.keyframes.get(cur)
        gi: Optional[QGraphicsItem] = self.win.object_manager.graphics_items.get(name)
        if kf is not None and gi is not None:
            attached_to = None
            parent = gi.parentItem()
            if parent:
                for key, val in self.win.object_manager.graphics_items.items():
                    if val is parent and ":" in key:
                        try:
                            puppet_name, member_name = key.split(":", 1)
                            attached_to = (puppet_name, member_name)
                            break
                        except ValueError as e:
                            logging.debug(
                                "Parsing puppet/member from key '%s' failed: %s", key, e
                            )
            state: dict[str, object] = obj.to_dict()
            try:
                state["x"] = float(gi.x())
                state["y"] = float(gi.y())
                state["rotation"] = float(gi.rotation())
                state["scale"] = float(gi.scale())
                state["z"] = int(gi.zValue())
            except RuntimeError as e:
                logging.debug(
                    "Reading graphics item state for '%s' failed: %s", name, e
                )
            state["attached_to"] = attached_to
            kf.objects[name] = state
        self.win.inspector_widget.refresh()
        return name

    def create_light_object(self, scene_pos: Optional[QPointF] = None) -> Optional[str]:
        """Creates a new light object and adds it to the scene."""
        base = "projecteur"
        name = self.unique_object_name(base)

        if scene_pos is None:
            c: QPointF = self.win.scene.sceneRect().center()
            x, y = c.x(), c.y() - 200  # Start it a bit higher
        else:
            x, y = float(scene_pos.x()), float(scene_pos.y())

        obj = SceneObject(
            name,
            obj_type="light",
            file_path="",  # No file for this type
            x=x,
            y=y,
            rotation=0,
            scale=1.0,
            z=100,  # High Z value to be on top
            color="#FFFFE0",
            cone_angle=45.0,
            cone_reach=500.0,
        )
        self.win.scene_model.add_object(obj)
        self._add_object_graphics(obj)
        cur: int = self.win.scene_model.current_frame
        if cur not in self.win.scene_model.keyframes:
            self.win.controller.add_keyframe(cur)
        kf: Optional[Keyframe] = self.win.scene_model.keyframes.get(cur)
        if kf is not None:
            kf.objects[name] = obj.to_dict()
        self.win.inspector_widget.refresh()
        return name

    def delete_object_from_current_frame(self, name: str) -> None:
        """
        Deletes an object from the current frame onwards by removing its state from keyframes.

        Args:
            name: The name of the object to delete.
        """
        cur: int = self.win.scene_model.current_frame
        if cur not in self.win.scene_model.keyframes:
            self.win.controller.add_keyframe(cur)
        for fr, kf in list(self.win.scene_model.keyframes.items()):
            if fr >= cur and name in kf.objects:
                del kf.objects[name]
        gi: Optional[QGraphicsItem] = self.win.object_manager.graphics_items.get(name)
        if gi:
            gi.setVisible(False)
