from __future__ import annotations
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene # Added QGraphicsScene

from core.scene_model import SceneObject, Keyframe, SceneModel
from core.puppet_model import Puppet, PuppetMember, PARENT_MAP, PIVOT_MAP, Z_ORDER
from core.svg_loader import SvgLoader
from ui.object_item import ObjectPixmapItem, ObjectSvgItem
from core.puppet_piece import PuppetPiece

if TYPE_CHECKING:
    from .main_window import MainWindow

from typing import Dict, Optional, Any

class ObjectManager:
    """Manages puppets and objects (creation, deletion, manipulation) in the scene."""
    def __init__(self, win: MainWindow) -> None:
        self.win: MainWindow = win
        self.scene: QGraphicsScene = win.scene
        self.scene_model: SceneModel = win.scene_model
        
        self.graphics_items: Dict[str, QGraphicsItem] = {}
        self.renderers: Dict[str, Any] = {} # QSvgRenderer is not directly imported
        self.puppet_scales: Dict[str, float] = {}
        self.puppet_paths: Dict[str, str] = {}

    def add_puppet(self, file_path: str, puppet_name: str) -> None:
        puppet: Puppet = Puppet(); loader: SvgLoader = SvgLoader(file_path); renderer: Any = loader.renderer # QSvgRenderer
        self.renderers[puppet_name] = renderer
        puppet.build_from_svg(loader, PARENT_MAP, PIVOT_MAP, Z_ORDER)
        self.scene_model.add_puppet(puppet_name, puppet)
        self.puppet_scales[puppet_name] = 1.0
        self.puppet_paths[puppet_name] = file_path
        self._add_puppet_graphics(puppet_name, puppet, file_path, renderer, loader)
        if hasattr(self.win, "inspector_widget"): self.win.inspector_widget.refresh()

    def _add_puppet_graphics(self, puppet_name: str, puppet: Puppet, file_path: str, renderer: Any, loader: SvgLoader) -> None:
        pieces: Dict[str, PuppetPiece] = {}
        for name, member in puppet.members.items():
            offset_x, offset_y = loader.get_group_offset(name) or (0.0, 0.0)
            pivot_x, pivot_y = member.pivot[0] - offset_x, member.pivot[1] - offset_y
            piece: PuppetPiece = PuppetPiece(file_path, name, pivot_x, pivot_y, renderer)
            piece.setZValue(member.z_order)
            pieces[name] = piece
            self.graphics_items[f"{puppet_name}:{name}"] = piece

        scene_center: QPointF = self.scene.sceneRect().center()
        for name, piece in pieces.items():
            member: PuppetMember = puppet.members[name]
            if member.parent:
                parent_piece: PuppetPiece = pieces[member.parent.name]
                piece.set_parent_piece(parent_piece, member.rel_pos[0], member.rel_pos[1])
            else: # Root piece
                offset_x, offset_y = loader.get_group_offset(name) or (0.0, 0.0)
                final_x: float = scene_center.x() - (member.pivot[0] - offset_x)
                final_y: float = scene_center.y() - (member.pivot[1] - offset_y)
                piece.setPos(final_x, final_y)
                piece.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)

        for piece in pieces.values():
            self.scene.addItem(piece); self.scene.addItem(piece.pivot_handle)
            if piece.rotation_handle: self.scene.addItem(piece.rotation_handle)

        for piece in pieces.values():
            if piece.parent_piece: piece.update_transform_from_parent()
            else: piece.update_handle_positions()

    def scale_puppet(self, puppet_name: str, ratio: float) -> None:
        puppet: Optional[Puppet] = self.scene_model.puppets.get(puppet_name)
        if not puppet: return
        for member_name in puppet.members:
            piece: Optional[PuppetPiece] = self.graphics_items.get(f"{puppet_name}:{member_name}")
            if not piece: continue
            piece.setScale(piece.scale() * ratio)
            if piece.parent_piece: piece.rel_to_parent = (piece.rel_to_parent[0] * ratio, piece.rel_to_parent[1] * ratio)
        for root_member in puppet.get_root_members():
            if (root_piece := self.graphics_items.get(f"{puppet_name}:{root_member.name}")):
                for child in root_piece.children: child.update_transform_from_parent()

    def delete_puppet(self, puppet_name: str) -> None:
        if (puppet := self.scene_model.puppets.get(puppet_name)):
            for member_name in list(puppet.members.keys()):
                if (piece := self.graphics_items.pop(f"{puppet_name}:{member_name}", None)):
                    self.scene.removeItem(piece)
                    if piece.pivot_handle: self.scene.removeItem(piece.pivot_handle)
                    if piece.rotation_handle: self.scene.removeItem(piece.rotation_handle)
            self.scene_model.remove_puppet(puppet_name)
            self.puppet_scales.pop(puppet_name, None)
            self.puppet_paths.pop(puppet_name, None)

    def duplicate_puppet(self, puppet_name: str) -> None:
        path: Optional[str] = self.puppet_paths.get(puppet_name)
        if not path: return
        base: str = puppet_name; i: int = 1
        new_name: str = f"{base}_{i}"
        while new_name in self.scene_model.puppets:
            i += 1
            new_name = f"{base}_{i}"
        self.add_puppet(path, new_name)
        scale: float = self.puppet_scales.get(puppet_name, 1.0)
        if scale != 1.0:
            self.puppet_scales[new_name] = scale
            self.scale_puppet(new_name, scale)

    def capture_puppet_states(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
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
            states[name] = puppet_state
        return states

    def delete_object(self, name: str) -> None:
        if (item := self.graphics_items.pop(name, None)): self.scene.removeItem(item)
        self.scene_model.remove_object(name)

    def duplicate_object(self, name: str) -> None:
        obj: Optional[SceneObject] = self.scene_model.objects.get(name)
        if not obj: return
        base: str = name; i: int = 1
        new_name: str = f"{base}_{i}"
        while new_name in self.scene_model.objects:
            i += 1
            new_name = f"{base}_{i}"
        new_obj: SceneObject = SceneObject(new_name, obj.obj_type, obj.file_path, x=obj.x + 10, y=obj.y + 10, rotation=obj.rotation, scale=obj.scale, z=getattr(obj, 'z', 0))
        self.scene_model.add_object(new_obj)
        self._add_object_graphics(new_obj)

    def _add_object_graphics(self, obj: SceneObject) -> None:
        item: QGraphicsItem
        if obj.obj_type == "image":
            item = ObjectPixmapItem(obj.file_path)
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
        # setTransformOriginPoint can fail if boundingRect is empty/invalid
        if not item.boundingRect().isEmpty():
            item.setTransformOriginPoint(item.boundingRect().center())
        else:
            logging.warning(f"Cannot set transform origin point for {obj.name}: bounding rect is empty.")
        # setZValue should not typically fail, but adding a check for robustness
        try:
            item.setZValue(getattr(obj, 'z', 0))
        except Exception as e:
            logging.error(f"Error setting Z-value for {obj.name}: {e}")
        item.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        self.scene.addItem(item)
        self.graphics_items[obj.name] = item

    def attach_object_to_member(self, obj_name: str, puppet_name: str, member_name: str) -> None:
        obj: Optional[SceneObject] = self.scene_model.objects.get(obj_name)
        item: Optional[QGraphicsItem] = self.graphics_items.get(obj_name)
        parent_piece: Optional[PuppetPiece] = self.graphics_items.get(f"{puppet_name}:{member_name}")
        if not obj or not item or not parent_piece:
            return
        self.win._suspend_item_updates = True
        try:
            scene_pt: QPointF = item.mapToScene(item.transformOriginPoint())
            item.setParentItem(parent_piece)
            local_pt: QPointF = parent_piece.mapFromScene(scene_pt)
            item.setPos(local_pt - item.transformOriginPoint())
        finally:
            self.win._suspend_item_updates = False
        # Persist local transform into the model
        obj.attach(puppet_name, member_name)
        try:
            obj.x = float(item.x()); obj.y = float(item.y())
            obj.rotation = float(item.rotation()); obj.scale = float(item.scale())
            obj.z = int(item.zValue())
        except Exception:
            pass
        kf: Optional[Keyframe] = self.scene_model.keyframes.get(self.scene_model.current_frame)
        if kf is not None:
            kf.objects[obj_name] = obj.to_dict()

    def detach_object(self, obj_name: str) -> None:
        obj: Optional[SceneObject] = self.scene_model.objects.get(obj_name)
        item: Optional[QGraphicsItem] = self.graphics_items.get(obj_name)
        if not obj or not item:
            return
        # Capture previous attachment to fix legacy keyframes with missing local coords
        prev_attachment = getattr(obj, 'attached_to', None)
        if prev_attachment is not None:
            try:
                # Item is currently attached: local x,y are meaningful
                local_x, local_y = float(item.x()), float(item.y())
                # For all keyframes up to current that reference this object with the same attachment,
                # ensure they store the same local coords so they won't fall back to (0,0)
                cur_idx: int = self.scene_model.current_frame
                for idx, kf in list(self.scene_model.keyframes.items()):
                    if idx <= cur_idx and obj_name in kf.objects:
                        st = kf.objects[obj_name]
                        if st.get('attached_to') == list(prev_attachment) or st.get('attached_to') == tuple(prev_attachment) or st.get('attached_to') == prev_attachment:
                            # Only patch if missing or 0,0 to avoid overwriting intentional anim edits
                            sx = st.get('x', 0.0); sy = st.get('y', 0.0)
                            try:
                                sx = float(sx); sy = float(sy)
                            except Exception:
                                sx, sy = 0.0, 0.0
                            if (abs(sx) < 1e-9 and abs(sy) < 1e-9):
                                st['x'] = local_x
                                st['y'] = local_y
                                kf.objects[obj_name] = st
            except Exception:
                pass
        self.win._suspend_item_updates = True
        try:
            scene_pt: QPointF = item.mapToScene(item.transformOriginPoint())
            item.setParentItem(None)
            item.setPos(scene_pt - item.transformOriginPoint())
        finally:
            self.win._suspend_item_updates = False
        # Persist world transform into the model
        obj.detach()
        try:
            obj.x = float(item.x()); obj.y = float(item.y())
            obj.rotation = float(item.rotation()); obj.scale = float(item.scale())
            obj.z = int(item.zValue())
        except Exception:
            pass
        kf: Optional[Keyframe] = self.scene_model.keyframes.get(self.scene_model.current_frame)
        if kf is not None:
            kf.objects[obj_name] = obj.to_dict()

    def _unique_object_name(self, base: str) -> str:
        name: str = base
        i: int = 1
        while name in self.scene_model.objects:
            name = f"{base}_{i}"
            i += 1
        return name

    def _unique_puppet_name(self, base: str) -> str:
        name: str = base
        i: int = 1
        while name in self.scene_model.puppets:
            name = f"{base}_{i}"
            i += 1
        return name

    def _create_object_from_file(self, file_path: str, scene_pos: Optional[QPointF] = None) -> Optional[str]:
        ext: str = Path(file_path).suffix.lower()
        obj_type: str
        if ext in ('.png', '.jpg', '.jpeg'):
            obj_type = 'image'
        elif ext == '.svg':
            obj_type = 'svg'
        else:
            logging.error(f"Unsupported object file type: {ext}")
            return None
        
        base: str = Path(file_path).stem
        name: str = self._unique_object_name(base)
        
        x: float
        y: float
        if scene_pos is None:
            c: QPointF = self.scene.sceneRect().center()
            x, y = c.x(), c.y()
        else:
            x, y = float(scene_pos.x()), float(scene_pos.y())

        obj: SceneObject = SceneObject(name, obj_type, file_path, x=x, y=y, rotation=0, scale=1.0, z=0)
        self.scene_model.add_object(obj)
        self._add_object_graphics(obj)
        # Ensure a keyframe exists, then persist the on-screen state derived from the graphics item
        cur: int = self.scene_model.current_frame
        if cur not in self.scene_model.keyframes:
            self.win.add_keyframe(cur)
        kf: Optional[Keyframe] = self.scene_model.keyframes.get(cur)
        gi: Optional[QGraphicsItem] = self.graphics_items.get(name)
        if kf is not None and gi is not None:
            # Determine attachment from parent
            attached_to = None
            parent = gi.parentItem()
            if parent:
                # Lookup owning puppet piece
                for key, val in self.graphics_items.items():
                    if val is parent and ":" in key:
                        try:
                            puppet_name, member_name = key.split(":", 1)
                            attached_to = (puppet_name, member_name)
                            break
                        except Exception:
                            pass
            state: Dict[str, Any] = obj.to_dict()
            try:
                state["x"] = float(gi.x()); state["y"] = float(gi.y())
                state["rotation"] = float(gi.rotation()); state["scale"] = float(gi.scale())
                state["z"] = int(gi.zValue())
            except Exception:
                pass
            state["attached_to"] = attached_to
            kf.objects[name] = state
        if hasattr(self.win, "inspector_widget"): self.win.inspector_widget.refresh()
        return name

    def _add_library_item_to_scene(self, payload: Dict[str, Any]) -> None:
        self._add_library_payload(payload, scene_pos=None)

    def handle_library_drop(self, payload: Dict[str, Any], pos: QPointF) -> None:
        scene_pt: QPointF = self.win.view.mapToScene(pos.toPoint())
        self._add_library_payload(payload, scene_pos=scene_pt)

    def _add_library_payload(self, payload: Dict[str, Any], scene_pos: Optional[QPointF]) -> None:
        kind: Optional[str] = payload.get('kind')
        path: Optional[str] = payload.get('path')
        if not kind or not path:
            return

        if kind == 'background':
            self.scene_model.background_path = path
            self.win._update_background()
        elif kind == 'object':
            self._create_object_from_file(path, scene_pos)
        elif kind == 'puppet':
            base: str = Path(path).stem
            name: str = self._unique_puppet_name(base)
            self.add_puppet(path, name)
            if scene_pos is not None:
                try:
                    root_member_name: str = self.scene_model.puppets[name].get_root_members()[0].name
                    root_piece: Optional[PuppetPiece] = self.graphics_items.get(f"{name}:{root_member_name}")
                    if root_piece:
                        root_piece.setPos(scene_pos.x(), scene_pos.y())
                except Exception as e:
                    logging.error(f"Positioning puppet failed: {e}")
        else:
            logging.error(f"Unknown library kind: {kind}")

    def delete_object_from_current_frame(self, name: str) -> None:
        cur: int = self.scene_model.current_frame
        if cur not in self.scene_model.keyframes:
            self.win.add_keyframe(cur)
        for fr, kf in list(self.scene_model.keyframes.items()):
            if fr >= cur and name in kf.objects:
                del kf.objects[name]
        gi: Optional[QGraphicsItem] = self.graphics_items.get(name)
        if gi:
            gi.setVisible(False)

    # --- Snapshot helpers ---
    def capture_visible_object_states(self) -> Dict[str, Dict[str, Any]]:
        """Capture the on-screen state for visible objects, including attachment derived from parentItem.
        Uses local coords when attached and scene coords when free (consistent with runtime usage).
        """
        states: Dict[str, Dict[str, Any]] = {}
        # Build a reverse map from PuppetPiece to (puppet, member)
        piece_owner: Dict[QGraphicsItem, tuple[str, str]] = {}
        for key, val in self.graphics_items.items():
            if isinstance(val, PuppetPiece) and ":" in key:
                try:
                    puppet_name, member_name = key.split(":", 1)
                    piece_owner[val] = (puppet_name, member_name)
                except Exception:
                    continue
        for name, obj in self.scene_model.objects.items():
            gi: Optional[QGraphicsItem] = self.graphics_items.get(name)
            if gi and gi.isVisible():
                parent = gi.parentItem()
                attached_to = None
                if parent in piece_owner:
                    attached_to = piece_owner[parent]
                data = obj.to_dict()
                try:
                    data["x"] = float(gi.x()); data["y"] = float(gi.y())
                    data["rotation"] = float(gi.rotation()); data["scale"] = float(gi.scale())
                    data["z"] = int(gi.zValue())
                except Exception:
                    pass
                data["attached_to"] = attached_to
                states[name] = data
        return states

    def snapshot_current_frame(self) -> None:
        cur: int = self.scene_model.current_frame
        puppet_states = self.capture_puppet_states()
        obj_states = self.capture_visible_object_states()
        kf: Optional[Keyframe] = self.scene_model.keyframes.get(cur)
        if kf is None:
            kf = Keyframe(cur)
        kf.puppets = puppet_states
        kf.objects = obj_states
        self.scene_model.keyframes[cur] = kf
        # Keep keyframes sorted
        self.scene_model.keyframes = dict(sorted(self.scene_model.keyframes.items()))
        # Ensure marker exists
        try:
            self.win.timeline_widget.add_keyframe_marker(cur)
        except Exception:
            pass
