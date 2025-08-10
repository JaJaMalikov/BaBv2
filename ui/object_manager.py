from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsItem

from core.scene_model import SceneObject
from core.puppet_model import Puppet, PARENT_MAP, PIVOT_MAP, Z_ORDER
from core.svg_loader import SvgLoader
from ui.object_item import ObjectPixmapItem, ObjectSvgItem
from core.puppet_piece import PuppetPiece

if TYPE_CHECKING:
    from .main_window import MainWindow

class ObjectManager:
    """Manages puppets and objects (creation, deletion, manipulation) in the scene."""
    def __init__(self, win: MainWindow):
        self.win = win
        self.scene = win.scene
        self.scene_model = win.scene_model
        
        self.graphics_items = {}
        self.renderers = {}
        self.puppet_scales = {}
        self.puppet_paths = {}

    def add_puppet(self, file_path, puppet_name):
        puppet = Puppet(); loader = SvgLoader(file_path); renderer = loader.renderer
        self.renderers[puppet_name] = renderer
        puppet.build_from_svg(loader, PARENT_MAP, PIVOT_MAP, Z_ORDER)
        self.scene_model.add_puppet(puppet_name, puppet)
        self.puppet_scales[puppet_name] = 1.0
        self.puppet_paths[puppet_name] = file_path
        self._add_puppet_graphics(puppet_name, puppet, file_path, renderer, loader)
        if hasattr(self.win, "inspector_widget"): self.win.inspector_widget.refresh()

    def _add_puppet_graphics(self, puppet_name, puppet, file_path, renderer, loader):
        pieces = {}
        for name, member in puppet.members.items():
            offset_x, offset_y = loader.get_group_offset(name) or (0, 0)
            pivot_x, pivot_y = member.pivot[0] - offset_x, member.pivot[1] - offset_y
            piece = PuppetPiece(file_path, name, pivot_x, pivot_y, renderer)
            piece.setZValue(member.z_order)
            pieces[name] = piece
            self.graphics_items[f"{puppet_name}:{name}"] = piece

        scene_center = self.scene.sceneRect().center()
        for name, piece in pieces.items():
            member = puppet.members[name]
            if member.parent:
                parent_piece = pieces[member.parent.name]
                piece.set_parent_piece(parent_piece, member.rel_pos[0], member.rel_pos[1])
            else: # Root piece
                offset_x, offset_y = loader.get_group_offset(name) or (0, 0)
                final_x = scene_center.x() - (member.pivot[0] - offset_x)
                final_y = scene_center.y() - (member.pivot[1] - offset_y)
                piece.setPos(final_x, final_y)
                piece.setFlag(QGraphicsItem.ItemIsMovable, True)
                piece.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

        for piece in pieces.values():
            self.scene.addItem(piece); self.scene.addItem(piece.pivot_handle)
            if piece.rotation_handle: self.scene.addItem(piece.rotation_handle)

        for piece in pieces.values():
            if piece.parent_piece: piece.update_transform_from_parent()
            else: piece.update_handle_positions()

    def scale_puppet(self, puppet_name, ratio):
        puppet = self.scene_model.puppets.get(puppet_name)
        if not puppet: return
        for member_name in puppet.members:
            piece = self.graphics_items.get(f"{puppet_name}:{member_name}")
            if not piece: continue
            piece.setScale(piece.scale() * ratio)
            if piece.parent_piece: piece.rel_to_parent = (piece.rel_to_parent[0] * ratio, piece.rel_to_parent[1] * ratio)
        for root_member in puppet.get_root_members():
            if (root_piece := self.graphics_items.get(f"{puppet_name}:{root_member.name}")):
                for child in root_piece.children: child.update_transform_from_parent()

    def delete_puppet(self, puppet_name):
        if (puppet := self.scene_model.puppets.get(puppet_name)):
            for member_name in list(puppet.members.keys()):
                if (piece := self.graphics_items.pop(f"{puppet_name}:{member_name}", None)):
                    self.scene.removeItem(piece)
                    if piece.pivot_handle: self.scene.removeItem(piece.pivot_handle)
                    if piece.rotation_handle: self.scene.removeItem(piece.rotation_handle)
            self.scene_model.remove_puppet(puppet_name)
            self.puppet_scales.pop(puppet_name, None)
            self.puppet_paths.pop(puppet_name, None)

    def duplicate_puppet(self, puppet_name):
        if not (path := self.puppet_paths.get(puppet_name)): return
        base = puppet_name; i = 1
        while (new_name := f"{base}_{i}") in self.scene_model.puppets: i += 1
        self.add_puppet(path, new_name)
        if (scale := self.puppet_scales.get(puppet_name, 1.0)) != 1.0:
            self.puppet_scales[new_name] = scale
            self.scale_puppet(new_name, scale)

    def capture_puppet_states(self):
        states = {}
        for name, puppet in self.scene_model.puppets.items():
            puppet_state = {}
            for member_name in puppet.members:
                piece = self.graphics_items.get(f"{name}:{member_name}")
                if piece:
                    puppet_state[member_name] = {
                        'rotation': piece.local_rotation,
                        'pos': (piece.x(), piece.y()),
                    }
            states[name] = puppet_state
        return states

    def delete_object(self, name):
        if (item := self.graphics_items.pop(name, None)): self.scene.removeItem(item)
        self.scene_model.remove_object(name)

    def duplicate_object(self, name):
        if not (obj := self.scene_model.objects.get(name)): return
        base = name; i = 1
        while (new_name := f"{base}_{i}") in self.scene_model.objects: i += 1
        new_obj = SceneObject(new_name, obj.obj_type, obj.file_path, x=obj.x + 10, y=obj.y + 10, rotation=obj.rotation, scale=obj.scale, z=getattr(obj, 'z', 0))
        self.scene_model.add_object(new_obj)
        self._add_object_graphics(new_obj)

    def _add_object_graphics(self, obj: SceneObject):
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
        try:
            item.setTransformOriginPoint(item.boundingRect().center())
        except Exception:
            pass
        try:
            item.setZValue(getattr(obj, 'z', 0))
        except Exception:
            pass
        item.setFlag(QGraphicsItem.ItemIsMovable, True); item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.scene.addItem(item)
        self.graphics_items[obj.name] = item

    def attach_object_to_member(self, obj_name: str, puppet_name: str, member_name: str):
        obj = self.scene_model.objects.get(obj_name)
        item = self.graphics_items.get(obj_name)
        parent_piece = self.graphics_items.get(f"{puppet_name}:{member_name}")
        if not obj or not item or not parent_piece:
            return
        self.win._suspend_item_updates = True
        try:
            scene_pt = item.mapToScene(item.transformOriginPoint())
            item.setParentItem(parent_piece)
            local_pt = parent_piece.mapFromScene(scene_pt)
            item.setPos(local_pt - item.transformOriginPoint())
        finally:
            self.win._suspend_item_updates = False
        obj.attach(puppet_name, member_name)
        kf = self.scene_model.keyframes.get(self.scene_model.current_frame)
        if kf is not None:
            kf.objects[obj_name] = obj.to_dict()

    def detach_object(self, obj_name: str):
        obj = self.scene_model.objects.get(obj_name)
        item = self.graphics_items.get(obj_name)
        if not obj or not item:
            return
        self.win._suspend_item_updates = True
        try:
            scene_pt = item.mapToScene(item.transformOriginPoint())
            item.setParentItem(None)
            item.setPos(scene_pt - item.transformOriginPoint())
        finally:
            self.win._suspend_item_updates = False
        obj.detach()
        kf = self.scene_model.keyframes.get(self.scene_model.current_frame)
        if kf is not None:
            kf.objects[obj_name] = obj.to_dict()

    def _unique_object_name(self, base: str) -> str:
        name = base
        i = 1
        while name in self.scene_model.objects:
            name = f"{base}_{i}"
            i += 1
        return name

    def _unique_puppet_name(self, base: str) -> str:
        name = base
        i = 1
        while name in self.scene_model.puppets:
            name = f"{base}_{i}"
            i += 1
        return name

    def _create_object_from_file(self, file_path: str, scene_pos: QPointF | None = None):
        ext = Path(file_path).suffix.lower()
        if ext in ('.png', '.jpg', '.jpeg'):
            obj_type = 'image'
        elif ext == '.svg':
            obj_type = 'svg'
        else:
            print(f"Unsupported object file type: {ext}")
            return None
        
        base = Path(file_path).stem
        name = self._unique_object_name(base)
        
        if scene_pos is None:
            c = self.scene.sceneRect().center()
            x, y = c.x(), c.y()
        else:
            x, y = float(scene_pos.x()), float(scene_pos.y())

        obj = SceneObject(name, obj_type, file_path, x=x, y=y, rotation=0, scale=1.0, z=0)
        self.scene_model.add_object(obj)
        self._add_object_graphics(obj)
        cur = self.scene_model.current_frame
        if cur not in self.scene_model.keyframes:
            self.win.add_keyframe(cur)
        kf = self.scene_model.keyframes.get(cur)
        if kf is not None:
            kf.objects[name] = obj.to_dict()
        if hasattr(self.win, "inspector_widget"): self.win.inspector_widget.refresh()
        return name

    def _add_library_item_to_scene(self, payload: dict):
        self._add_library_payload(payload, scene_pos=None)

    def handle_library_drop(self, payload: dict, pos: QPointF):
        scene_pt = self.win.view.mapToScene(pos.toPoint())
        self._add_library_payload(payload, scene_pos=scene_pt)

    def _add_library_payload(self, payload: dict, scene_pos: QPointF | None):
        kind = payload.get('kind')
        path = payload.get('path')
        if not kind or not path:
            return

        if kind == 'background':
            self.scene_model.background_path = path
            self.win._update_background()
        elif kind == 'object':
            self._create_object_from_file(path, scene_pos)
        elif kind == 'puppet':
            base = Path(path).stem
            name = self._unique_puppet_name(base)
            self.add_puppet(path, name)
            if scene_pos is not None:
                try:
                    root_member_name = self.scene_model.puppets[name].get_root_members()[0].name
                    root_piece = self.graphics_items.get(f"{name}:{root_member_name}")
                    if root_piece:
                        root_piece.setPos(scene_pos.x(), scene_pos.y())
                except Exception as e:
                    print(f"Positioning puppet failed: {e}")
        else:
            print(f"Unknown library kind: {kind}")

    def delete_object_from_current_frame(self, name: str):
        cur = self.scene_model.current_frame
        if cur not in self.scene_model.keyframes:
            self.win.add_keyframe(cur)
        for fr, kf in list(self.scene_model.keyframes.items()):
            if fr >= cur and name in kf.objects:
                del kf.objects[name]
        if (gi := self.graphics_items.get(name)):
            gi.setVisible(False)
