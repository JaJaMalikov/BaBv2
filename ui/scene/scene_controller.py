"""SceneController: façade légère pour regrouper les opérations de scène.

Objectif de ce premier incrément:
- Centraliser l'accès à StateApplier, SceneVisuals et OnionSkinManager
- Exposer de petites méthodes de délégation sans changer le comportement
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsItem

from core.puppet_model import PARENT_MAP, PIVOT_MAP, Z_ORDER, Puppet, PuppetMember
from core.puppet_piece import PuppetPiece
from core.scene_model import Keyframe, SceneObject
from core.svg_loader import SvgLoader
from ..object_item import ObjectPixmapItem, ObjectSvgItem
from .state_applier import StateApplier
from .scene_visuals import SceneVisuals
from ..onion_skin import OnionSkinManager


class SceneController:
    """A facade for grouping scene operations."""
    def __init__(self, win: Any, *, visuals: SceneVisuals | None = None, onion: OnionSkinManager | None = None, applier: StateApplier | None = None) -> None:
        """Initializes the scene controller.

        Args:
            win: The main window of the application.
            visuals: The scene visuals manager.
            onion: The onion skin manager.
            applier: The state applier.
        """
        self.win = win
        # Conserver les instances existantes si fournies pour éviter tout double initialisation
        self.visuals: SceneVisuals = visuals if visuals is not None else SceneVisuals(win)
        # S'assurer que setup est appelé si la visualisation est créée ici
        if visuals is None:
            self.visuals.setup()

        self.onion: OnionSkinManager = onion if onion is not None else OnionSkinManager(win)
        self.applier: StateApplier = applier if applier is not None else StateApplier(win)

    # --- Scene manipulation ---
    def add_puppet(self, file_path: str, puppet_name: str) -> None:
        """Adds a puppet to the scene.

        Args:
            file_path: The path to the puppet's SVG file.
            puppet_name: The name of the puppet.
        """
        puppet: Puppet = Puppet()
        loader: SvgLoader = SvgLoader(file_path)
        renderer: Any = loader.renderer  # QSvgRenderer
        self.win.object_manager.renderers[puppet_name] = renderer
        puppet.build_from_svg(loader, PARENT_MAP, PIVOT_MAP, Z_ORDER)
        self.win.scene_model.add_puppet(puppet_name, puppet)
        self.win.object_manager.puppet_scales[puppet_name] = 1.0
        self.win.object_manager.puppet_paths[puppet_name] = file_path
        self.win.object_manager.puppet_z_offsets[puppet_name] = 0
        self._add_puppet_graphics(puppet_name, puppet, file_path, renderer, loader)
        if hasattr(self.win, "inspector_widget"):
            self.win.inspector_widget.refresh()

    def _add_puppet_graphics(self, puppet_name: str, puppet: Puppet, file_path: str, renderer: Any, loader: SvgLoader) -> None:
        """Adds the graphical representation of a puppet to the scene."""
        pieces: Dict[str, PuppetPiece] = {}
        for name, member in puppet.members.items():
            offset_x, offset_y = loader.get_group_offset(name) or (0.0, 0.0)
            pivot_x, pivot_y = member.pivot[0] - offset_x, member.pivot[1] - offset_y
            piece: PuppetPiece = PuppetPiece(file_path, name, pivot_x, pivot_y, renderer)
            piece.setZValue(member.z_order)
            pieces[name] = piece
            self.win.object_manager.graphics_items[f"{puppet_name}:{name}"] = piece

        scene_center: QPointF = self.win.scene.sceneRect().center()
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
                piece.setFlag(QGraphicsItem.ItemIsMovable, True)
                piece.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

        for piece in pieces.values():
            self.win.scene.addItem(piece)
            self.win.scene.addItem(piece.pivot_handle)
            if piece.rotation_handle:
                self.win.scene.addItem(piece.rotation_handle)

        for piece in pieces.values():
            if piece.parent_piece:
                piece.update_transform_from_parent()
            else:
                piece.update_handle_positions()

        # Apply z offset if any (default 0)
        zoff: int = self.win.object_manager.puppet_z_offsets.get(puppet_name, 0)
        if zoff:
            for name, piece in pieces.items():
                member = puppet.members[name]
                try:
                    piece.setZValue(member.z_order + zoff)
                except Exception:
                    pass

    def scale_puppet(self, puppet_name: str, ratio: float) -> None:
        """Scales a puppet by a given ratio."""
        puppet: Optional[Puppet] = self.win.scene_model.puppets.get(puppet_name)
        if not puppet:
            return
        for member_name in puppet.members:
            piece: Optional[PuppetPiece] = self.win.object_manager.graphics_items.get(f"{puppet_name}:{member_name}")
            if not piece:
                continue
            piece.setScale(piece.scale() * ratio)
            if piece.parent_piece:
                piece.rel_to_parent = (piece.rel_to_parent[0] * ratio, piece.rel_to_parent[1] * ratio)
        for root_member in puppet.get_root_members():
            if (root_piece := self.win.object_manager.graphics_items.get(f"{puppet_name}:{root_member.name}")):
                for child in root_piece.children:
                    child.update_transform_from_parent()

    def delete_puppet(self, puppet_name: str) -> None:
        """Deletes a puppet from the scene."""
        if (puppet := self.win.scene_model.puppets.get(puppet_name)):
            for member_name in list(puppet.members.keys()):
                if (piece := self.win.object_manager.graphics_items.pop(f"{puppet_name}:{member_name}", None)):
                    self.win.scene.removeItem(piece)
                    if piece.pivot_handle:
                        self.win.scene.removeItem(piece.pivot_handle)
                    if piece.rotation_handle:
                        self.win.scene.removeItem(piece.rotation_handle)
            self.win.scene_model.remove_puppet(puppet_name)
            self.win.object_manager.puppet_scales.pop(puppet_name, None)
            self.win.object_manager.puppet_paths.pop(puppet_name, None)
            self.win.object_manager.puppet_z_offsets.pop(puppet_name, None)

    def duplicate_puppet(self, puppet_name: str) -> None:
        """Duplicates a puppet."""
        path: Optional[str] = self.win.object_manager.puppet_paths.get(puppet_name)
        if not path:
            return
        base: str = puppet_name
        i: int = 1
        new_name: str = f"{base}_{i}"
        while new_name in self.win.scene_model.puppets:
            i += 1
            new_name = f"{base}_{i}"
        self.add_puppet(path, new_name)
        scale: float = self.win.object_manager.puppet_scales.get(puppet_name, 1.0)
        if scale != 1.0:
            self.win.object_manager.puppet_scales[new_name] = scale
            self.scale_puppet(new_name, scale)
        zoff: int = self.win.object_manager.puppet_z_offsets.get(puppet_name, 0)
        if zoff:
            self.set_puppet_z_offset(new_name, zoff)

    def _puppet_root_piece(self, puppet_name: str) -> Optional[PuppetPiece]:
        """Returns the root piece of a puppet."""
        puppet: Optional[Puppet] = self.win.scene_model.puppets.get(puppet_name)
        if not puppet:
            return None
        roots = puppet.get_root_members()
        if not roots:
            return None
        return self.win.object_manager.graphics_items.get(f"{puppet_name}:{roots[0].name}")  # type: ignore

    def get_puppet_rotation(self, puppet_name: str) -> float:
        """Returns the rotation of a puppet."""
        rp = self._puppet_root_piece(puppet_name)
        if isinstance(rp, PuppetPiece):
            return float(rp.local_rotation)
        return 0.0

    def set_puppet_rotation(self, puppet_name: str, angle: float) -> None:
        """Sets the rotation of a puppet."""
        rp = self._puppet_root_piece(puppet_name)
        if isinstance(rp, PuppetPiece):
            rp.rotate_piece(float(angle))

    def set_puppet_z_offset(self, puppet_name: str, offset: int) -> None:
        """Sets the Z-offset of a puppet."""
        puppet: Optional[Puppet] = self.win.scene_model.puppets.get(puppet_name)
        if not puppet:
            return
        self.win.object_manager.puppet_z_offsets[puppet_name] = int(offset)
        for member_name, member in puppet.members.items():
            piece: Optional[PuppetPiece] = self.win.object_manager.graphics_items.get(f"{puppet_name}:{member_name}")
            if piece:
                try:
                    piece.setZValue(member.z_order + int(offset))
                except Exception:
                    pass

    def delete_object(self, name: str) -> None:
        """Deletes an object from the scene."""
        if (item := self.win.object_manager.graphics_items.pop(name, None)):
            self.win.scene.removeItem(item)
        self.win.scene_model.remove_object(name)

    def duplicate_object(self, name: str) -> None:
        """Duplicates an object."""
        obj: Optional[SceneObject] = self.win.scene_model.objects.get(name)
        if not obj:
            return
        base: str = name
        i: int = 1
        new_name: str = f"{base}_{i}"
        while new_name in self.win.scene_model.objects:
            i += 1
            new_name = f"{base}_{i}"
        new_obj: SceneObject = SceneObject(new_name, obj.obj_type, obj.file_path, x=obj.x + 10, y=obj.y + 10, rotation=obj.rotation, scale=obj.scale, z=getattr(obj, 'z', 0))
        self.win.scene_model.add_object(new_obj)
        self._add_object_graphics(new_obj)

    def _add_object_graphics(self, obj: SceneObject) -> None:
        """Adds the graphical representation of an object to the scene."""
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
        item.setFlag(QGraphicsItem.ItemIsMovable, True)
        item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.win.scene.addItem(item)
        self.win.object_manager.graphics_items[obj.name] = item

    def attach_object_to_member(self, obj_name: str, puppet_name: str, member_name: str) -> None:
        """Attaches an object to a puppet member."""
        obj: Optional[SceneObject] = self.win.scene_model.objects.get(obj_name)
        item: Optional[QGraphicsItem] = self.win.object_manager.graphics_items.get(obj_name)
        parent_piece: Optional[PuppetPiece] = self.win.object_manager.graphics_items.get(f"{puppet_name}:{member_name}")
        if not obj or not item or not parent_piece:
            return
        # Compute world transform components before parenting
        from math import atan2, degrees, sqrt
        wt = item.sceneTransform()
        m11, m12, m21, m22 = float(wt.m11()), float(wt.m12()), float(wt.m21()), float(wt.m22())
        world_rot = degrees(atan2(m12, m11))
        world_sx = sqrt(m11 * m11 + m21 * m21)
        # Y scale cannot be negative with our usage; fall back to sx if degenerate
        world_sy = sqrt(m12 * m12 + m22 * m22) if (m12 or m22) else world_sx
        scene_pt: QPointF = item.mapToScene(item.transformOriginPoint())

        # Parent world components
        pt = parent_piece.sceneTransform()
        pm11, pm12, pm21, pm22 = float(pt.m11()), float(pt.m12()), float(pt.m21()), float(pt.m22())
        parent_rot = degrees(atan2(pm12, pm11))
        parent_sx = sqrt(pm11 * pm11 + pm21 * pm21)
        parent_sy = sqrt(pm12 * pm12 + pm22 * pm22) if (pm12 or pm22) else parent_sx

        self.win._suspend_item_updates = True
        try:
            item.setParentItem(parent_piece)
            # Set local rotation/scale so the world transform remains the same at the moment of attach
            try:
                item.setRotation(world_rot - parent_rot)
                # Use uniform scale from X to avoid distortions
                lx = world_sx / (parent_sx if parent_sx != 0 else 1.0)
                ly = world_sy / (parent_sy if parent_sy != 0 else 1.0)
                # Prefer uniform scaling: pick average
                lscale = (lx + ly) * 0.5 if ly > 0 else lx
                item.setScale(lscale)
            except Exception:
                pass
            local_pt: QPointF = parent_piece.mapFromScene(scene_pt)
            item.setPos(local_pt - item.transformOriginPoint())
        finally:
            self.win._suspend_item_updates = False
        # Persist local transform into the model and ensure a keyframe exists
        obj.attach(puppet_name, member_name)
        try:
            obj.x = float(item.x())
            obj.y = float(item.y())
            obj.rotation = float(item.rotation())
            obj.scale = float(item.scale())
            obj.z = int(item.zValue())
        except Exception as e:
            logging.debug("Failed to read item transform on attach for '%s': %s", obj_name, e)
        cur_idx = self.win.scene_model.current_frame
        if cur_idx not in self.win.scene_model.keyframes:
            self.win.add_keyframe(cur_idx)
        kf: Optional[Keyframe] = self.win.scene_model.keyframes.get(cur_idx)
        if kf is not None:
            kf.objects[obj_name] = obj.to_dict()

    def detach_object(self, obj_name: str) -> None:
        """Detaches an object from its parent."""
        obj: Optional[SceneObject] = self.win.scene_model.objects.get(obj_name)
        item: Optional[QGraphicsItem] = self.win.object_manager.graphics_items.get(obj_name)
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
                cur_idx: int = self.win.scene_model.current_frame
                for idx, kf in list(self.win.scene_model.keyframes.items()):
                    if idx <= cur_idx and obj_name in kf.objects:
                        st = kf.objects[obj_name]
                        if st.get('attached_to') == list(prev_attachment) or st.get('attached_to') == tuple(prev_attachment) or st.get('attached_to') == prev_attachment:
                            # Only patch if missing or 0,0 to avoid overwriting intentional anim edits
                            sx = st.get('x', 0.0)
                            sy = st.get('y', 0.0)
                            try:
                                sx = float(sx)
                                sy = float(sy)
                            except (TypeError, ValueError):
                                sx, sy = 0.0, 0.0
                            if (abs(sx) < 1e-9 and abs(sy) < 1e-9):
                                st['x'] = local_x
                                st['y'] = local_y
                                kf.objects[obj_name] = st
            except Exception as e:
                logging.debug("While patching legacy keyframes for '%s': %s", obj_name, e)
        # Bake world rotation/scale/z to avoid visual jump on detach
        from math import atan2, degrees, sqrt
        wt = item.sceneTransform()
        m11, m12, m21, m22 = float(wt.m11()), float(wt.m12()), float(wt.m21()), float(wt.m22())
        world_rot = degrees(atan2(m12, m11))
        world_sx = sqrt(m11 * m11 + m21 * m21)
        world_sy = sqrt(m12 * m12 + m22 * m22) if (m12 or m22) else world_sx
        scene_pt: QPointF = item.mapToScene(item.transformOriginPoint())
        parent_z = item.parentItem().zValue() if item.parentItem() is not None else 0.0

        self.win._suspend_item_updates = True
        try:
            item.setParentItem(None)
            try:
                # Prefer uniform scale as before
                lscale = (world_sx + world_sy) * 0.5
                item.setScale(lscale)
                item.setRotation(world_rot)
            except Exception:
                pass
            try:
                item.setZValue(float(item.zValue()) + float(parent_z))
            except Exception:
                pass
            item.setPos(scene_pt - item.transformOriginPoint())
        finally:
            self.win._suspend_item_updates = False
        # Persist world transform into the model
        obj.detach()
        try:
            obj.x = float(item.x())
            obj.y = float(item.y())
            obj.rotation = float(item.rotation())
            obj.scale = float(item.scale())
            obj.z = int(item.zValue())
        except Exception as e:
            logging.debug("Failed to read item transform on detach for '%s': %s", obj_name, e)
        cur_idx = self.win.scene_model.current_frame
        if cur_idx not in self.win.scene_model.keyframes:
            self.win.add_keyframe(cur_idx)
        kf: Optional[Keyframe] = self.win.scene_model.keyframes.get(cur_idx)
        if kf is not None:
            kf.objects[obj_name] = obj.to_dict()

    def _unique_object_name(self, base: str) -> str:
        """Generates a unique name for an object."""
        name: str = base
        i: int = 1
        while name in self.win.scene_model.objects:
            name = f"{base}_{i}"
            i += 1
        return name

    def _unique_puppet_name(self, base: str) -> str:
        """Generates a unique name for a puppet."""
        name: str = base
        i: int = 1
        while name in self.win.scene_model.puppets:
            name = f"{base}_{i}"
            i += 1
        return name

    def _create_object_from_file(self, file_path: str, scene_pos: Optional[QPointF] = None) -> Optional[str]:
        """Creates an object from a file."""
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
            c: QPointF = self.win.scene.sceneRect().center()
            x, y = c.x(), c.y()
        else:
            x, y = float(scene_pos.x()), float(scene_pos.y())

        obj: SceneObject = SceneObject(name, obj_type, file_path, x=x, y=y, rotation=0, scale=1.0, z=0)
        self.win.scene_model.add_object(obj)
        self._add_object_graphics(obj)
        # Ensure a keyframe exists, then persist the on-screen state derived from the graphics item
        cur: int = self.win.scene_model.current_frame
        if cur not in self.win.scene_model.keyframes:
            self.win.add_keyframe(cur)
        kf: Optional[Keyframe] = self.win.scene_model.keyframes.get(cur)
        gi: Optional[QGraphicsItem] = self.win.object_manager.graphics_items.get(name)
        if kf is not None and gi is not None:
            # Determine attachment from parent
            attached_to = None
            parent = gi.parentItem()
            if parent:
                # Lookup owning puppet piece
                for key, val in self.win.object_manager.graphics_items.items():
                    if val is parent and ":" in key:
                        try:
                            puppet_name, member_name = key.split(":", 1)
                            attached_to = (puppet_name, member_name)
                            break
                        except Exception as e:
                            logging.debug("Parsing puppet/member from key '%s' failed: %s", key, e)
            state: Dict[str, Any] = obj.to_dict()
            try:
                state["x"] = float(gi.x())
                state["y"] = float(gi.y())
                state["rotation"] = float(gi.rotation())
                state["scale"] = float(gi.scale())
                state["z"] = int(gi.zValue())
            except Exception as e:
                logging.debug("Reading graphics item state for '%s' failed: %s", name, e)
            state["attached_to"] = attached_to
            kf.objects[name] = state
        if hasattr(self.win, "inspector_widget"):
            self.win.inspector_widget.refresh()
        return name

    def _add_library_item_to_scene(self, payload: Dict[str, Any]) -> None:
        """Adds a library item to the scene."""
        self._add_library_payload(payload, scene_pos=None)

    def handle_library_drop(self, payload: Dict[str, Any], pos: QPointF) -> None:
        """Handles a library item drop event."""
        scene_pt: QPointF = self.win.view.mapToScene(pos.toPoint())
        self._add_library_payload(payload, scene_pos=scene_pt)

    def _add_library_payload(self, payload: Dict[str, Any], scene_pos: Optional[QPointF]) -> None:
        """Adds a library payload to the scene."""
        kind: Optional[str] = payload.get('kind')
        path: Optional[str] = payload.get('path')
        if not kind or not path:
            return

        if kind == 'background':
            try:
                self.set_background_path(path)
            except Exception:
                # Fallback for older code paths
                self.win.scene_model.background_path = path
                self.win._update_background()
        elif kind == 'object':
            self._create_object_from_file(path, scene_pos)
        elif kind == 'puppet':
            base: str = Path(path).stem
            name: str = self._unique_puppet_name(base)
            self.add_puppet(path, name)
            if scene_pos is not None:
                try:
                    root_member_name: str = self.win.scene_model.puppets[name].get_root_members()[0].name
                    root_piece: Optional[PuppetPiece] = self.win.object_manager.graphics_items.get(f"{name}:{root_member_name}")
                    if root_piece:
                        root_piece.setPos(scene_pos.x(), scene_pos.y())
                except Exception as e:
                    logging.error(f"Positioning puppet failed: {e}")
        else:
            logging.error(f"Unknown library kind: {kind}")

    def delete_object_from_current_frame(self, name: str) -> None:
        """Deletes an object from the current frame onwards."""
        cur: int = self.win.scene_model.current_frame
        if cur not in self.win.scene_model.keyframes:
            self.win.add_keyframe(cur)
        for fr, kf in list(self.win.scene_model.keyframes.items()):
            if fr >= cur and name in kf.objects:
                del kf.objects[name]
        gi: Optional[QGraphicsItem] = self.win.object_manager.graphics_items.get(name)
        if gi:
            gi.setVisible(False)

    # --- Délégations visuelles ---
    def update_scene_visuals(self) -> None:
        """Updates the scene visuals."""
        self.visuals.update_scene_visuals()

    def update_background(self) -> None:
        """Updates the background."""
        self.visuals.update_background()
    def set_background_path(self, path: Optional[str]) -> None:
        """Set background image path and refresh visuals accordingly."""
        self.win.scene_model.background_path = path
        self.update_background()
	# --- Zoom & ajustements de vue ---
    def zoom(self, factor: float) -> None:
        """Applique un zoom sur la vue et met à jour le statut."""
        self.win.view.scale(factor, factor)
        self.win.zoom_factor *= factor
        try:
            self.win._update_zoom_status()
        except Exception:
            pass

    # --- Délégations onion skin ---
    def set_onion_enabled(self, enabled: bool) -> None:
        """Enables or disables onion skinning."""
        self.onion.set_enabled(enabled)

    def clear_onion_skins(self) -> None:
        """Clears the onion skins."""
        self.onion.clear()

    def update_onion_skins(self) -> None:
        """Updates the onion skins."""
        self.onion.update()

    # --- Poignées de rotation ---
    def set_rotation_handles_visible(self, visible: bool) -> None:
        """Afficher ou masquer les poignées de rotation des pantins."""
        for item in self.win.object_manager.graphics_items.values():
            if isinstance(item, PuppetPiece):
                item.set_handle_visibility(visible)
        try:
            self.win.view.handles_btn.setChecked(visible)
        except Exception:
            pass

    # --- Application d'états (keyframes) ---
    def apply_puppet_states(self, graphics_items: Dict[str, Any], keyframes: Dict[int, Any], index: int) -> None:
        """Applies puppet states from a keyframe to the scene."""
        self.applier.apply_puppet_states(graphics_items, keyframes, index)

    def apply_object_states(self, graphics_items: Dict[str, Any], keyframes: Dict[int, Any], index: int) -> None:
        """Applies object states from a keyframe to the scene."""
        self.applier.apply_object_states(graphics_items, keyframes, index)

    # --- Réglages scène ---
    def set_scene_size(self, width: int, height: int) -> None:
        """Ajuste la taille de la scène et rafraîchit les visuels.

        Conserve le comportement historique: met à jour la rect, rafraîchit visuels,
        relance l'arrière-plan (qui peut réimposer une taille selon l'image) et met à jour le zoom.
        """
        self.win.scene_model.scene_width = int(width)
        self.win.scene_model.scene_height = int(height)
        self.win.scene.setSceneRect(0, 0, int(width), int(height))
        self.update_scene_visuals()
        self.update_background()
        try:
            self.win._update_zoom_status()
        except Exception:
            pass
