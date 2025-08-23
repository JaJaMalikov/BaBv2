"""Module for managing onion skinning in the scene.

This module provides the `OnionSkinManager` class, which is responsible for
displaying semi-transparent 'ghosts' of puppets and objects from previous
and next frames.
"""

from __future__ import annotations

import logging
import math
from typing import Dict, Optional, Any, List

logger = logging.getLogger(__name__)

from PySide6.QtWidgets import QGraphicsItem, QGraphicsPixmapItem
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QPointF

from core.scene_model import Keyframe
from ui.scene.puppet_piece import PuppetPiece


class OnionSkinManager:
    """Encapsule la logique d'affichage des fantômes (onion skin).

    Délègue aux composants existants de MainWindow pour l'accès à la scène,
    au modèle et aux items graphiques.
    """

    def __init__(
        self, main_window: "Any"
    ) -> None:  # avoid circular import in type hints
        """Initializes the onion skin manager.

        Args:
            main_window: The main window of the application.
        """
        self.win = main_window
        self.enabled: bool = False
        self.prev_count: int = 2
        self.next_count: int = 1
        self.opacity_prev: float = 0.25
        self.opacity_next: float = 0.18
        self._onion_items: List[QGraphicsItem] = []

    # --- Public API ---
    def set_enabled(self, enabled: bool) -> None:
        """Enables or disables onion skinning."""
        self.enabled = enabled
        self.update()

    def clear(self) -> None:
        """Clears all onion skin items from the scene."""
        # Remove only root onion items to avoid Qt warnings when children lose their scene
        for it in list(self._onion_items):
            try:
                if it and it.parentItem() is None and it.scene() is self.win.scene:
                    self.win.scene.removeItem(it)
            except RuntimeError as e:
                logger.debug("Failed removing onion item: %s", e)
        self._onion_items.clear()

    def update(self) -> None:
        """Updates the onion skins based on the current frame."""
        self.clear()
        if not self.enabled:
            return
        cur: int = self.win.scene_model.current_frame
        # Previous frames
        for k in range(1, self.prev_count + 1):
            idx = max(self.win.scene_model.start_frame, cur - k)
            if idx == cur:
                continue
            self._add_onion_for_frame(idx, self.opacity_prev, z_offset=-200)
        # Next frames
        for k in range(1, self.next_count + 1):
            idx = min(self.win.scene_model.end_frame, cur + k)
            if idx == cur:
                continue
            self._add_onion_for_frame(idx, self.opacity_next, z_offset=-300)

    def _clone_puppet(
        self, puppet_name, puppet, kf, opacity, z_offset
    ) -> Dict[str, PuppetPiece]:
        puppet_state: Dict[str, Dict[str, Any]] = kf.puppets.get(puppet_name, {})
        if not puppet_state:
            return {}

        clones: Dict[str, PuppetPiece] = {}
        graphics_items: Dict[str, Any] = self.win.object_manager.graphics_items
        scale_factor: float = float(
            self.win.object_manager.puppet_scales.get(puppet_name, 1.0) or 1.0
        )

        for member_name in puppet.members:
            base_piece: PuppetPiece = graphics_items.get(f"{puppet_name}:{member_name}")
            if not base_piece:
                continue

            clone: PuppetPiece = PuppetPiece(
                "",
                member_name,
                base_piece.transformOriginPoint().x(),
                base_piece.transformOriginPoint().y(),
                renderer=self.win.object_manager.renderers.get(puppet_name),
            )
            clone.setOpacity(opacity)
            clone.setZValue(base_piece.zValue() + z_offset)
            clone.setFlag(QGraphicsItem.ItemIsSelectable, False)
            clone.setFlag(QGraphicsItem.ItemIsMovable, False)
            if scale_factor != 1.0:
                clone.setScale(scale_factor)
            self.win.scene.addItem(clone)
            self._onion_items.append(clone)
            clones[member_name] = clone

        for root_member in puppet.get_root_members():
            root_name = root_member.name
            clone_root: Optional[PuppetPiece] = clones.get(root_name)
            state = puppet_state.get(root_name)
            if clone_root is None or state is None:
                continue
            clone_root.setPos(*state.get("pos", (clone_root.x(), clone_root.y())))
            clone_root.setRotation(state.get("rotation", 0.0))

        def propagate(
            member_name: str, p_puppet_name, p_clones, p_scale_factor, p_puppet_state
        ):
            base_piece: PuppetPiece = graphics_items.get(
                f"{p_puppet_name}:{member_name}"
            )
            clone_piece: PuppetPiece = p_clones.get(member_name)
            if not base_piece or not clone_piece:
                return
            for child in base_piece.children:
                child_clone: Optional[PuppetPiece] = p_clones.get(child.name)
                if child_clone is None:
                    continue
                parent_rot: float = clone_piece.rotation()
                angle_rad: float = parent_rot * math.pi / 180.0
                member_def = puppet.members.get(child.name)
                if member_def is not None:
                    dx, dy = member_def.rel_pos
                else:
                    dx, dy = child.rel_to_parent
                if p_scale_factor != 1.0:
                    dx *= p_scale_factor
                    dy *= p_scale_factor
                cos_a = math.cos(angle_rad)
                sin_a = math.sin(angle_rad)
                rotated_dx: float = dx * cos_a - dy * sin_a
                rotated_dy: float = dx * sin_a + dy * cos_a
                parent_pivot_scene: QPointF = clone_piece.mapToScene(
                    clone_piece.transformOriginPoint()
                )
                scene_x: float = parent_pivot_scene.x() + rotated_dx
                scene_y: float = parent_pivot_scene.y() + rotated_dy
                child_clone.setPos(
                    scene_x - child_clone.transformOriginPoint().x(),
                    scene_y - child_clone.transformOriginPoint().y(),
                )
                child_state = p_puppet_state.get(child.name, {})
                child_clone.setRotation(parent_rot + child_state.get("rotation", 0.0))
                propagate(
                    child.name, p_puppet_name, p_clones, p_scale_factor, p_puppet_state
                )

        for root_member in puppet.get_root_members():
            propagate(root_member.name, puppet_name, clones, scale_factor, puppet_state)

        return clones

    def _clone_object(
        self, name, base_obj, kf, opacity, z_offset, clones_map, frame_index
    ):
        keyframes = self.win.scene_model.keyframes
        si: List[int] = sorted(keyframes.keys())
        last_kf: Optional[int] = next(
            (i for i in reversed(si) if i <= frame_index), None
        )
        if last_kf is not None and name not in keyframes[last_kf].objects:
            return
        prev_including: Optional[int] = next(
            (
                i
                for i in reversed(si)
                if i <= frame_index and name in keyframes[i].objects
            ),
            None,
        )
        if prev_including is None:
            return
        st = keyframes[prev_including].objects.get(name)

        if not st:
            return
        try:
            if st.get("obj_type") == "image":
                pm = QPixmap(st.get("file_path", base_obj.file_path))
                item: QGraphicsItem = QGraphicsPixmapItem(pm)
            else:
                item = QGraphicsSvgItem(st.get("file_path", base_obj.file_path))
            item.setFlag(QGraphicsItem.ItemIsMovable, False)
            item.setFlag(QGraphicsItem.ItemIsSelectable, False)
            item.setOpacity(opacity)
            if hasattr(item, "boundingRect") and not item.boundingRect().isEmpty():
                item.setTransformOriginPoint(item.boundingRect().center())
            attached = st.get("attached_to")
            if attached:
                try:
                    puppet_name, member_name = attached
                    parent_clone: Optional[PuppetPiece] = clones_map.get(
                        f"{puppet_name}:{member_name}"
                    )
                    if parent_clone is not None:
                        item.setParentItem(parent_clone)
                        item.setScale(st.get("scale", getattr(base_obj, "scale", 1.0)))
                        item.setRotation(
                            st.get("rotation", getattr(base_obj, "rotation", 0.0))
                        )
                        item.setZValue(
                            st.get("z", getattr(base_obj, "z", 0)) + z_offset
                        )
                        item.setPos(
                            st.get("x", getattr(base_obj, "x", 0.0)),
                            st.get("y", getattr(base_obj, "y", 0.0)),
                        )
                    else:
                        item.setScale(st.get("scale", getattr(base_obj, "scale", 1.0)))
                        item.setRotation(
                            st.get("rotation", getattr(base_obj, "rotation", 0.0))
                        )
                        item.setZValue(
                            st.get("z", getattr(base_obj, "z", 0)) + z_offset
                        )
                        item.setPos(
                            st.get("x", getattr(base_obj, "x", 0.0)),
                            st.get("y", getattr(base_obj, "y", 0.0)),
                        )
                        self.win.scene.addItem(item)
                        self._onion_items.append(item)
                except (RuntimeError, AttributeError, KeyError) as e:
                    logger.error("Onion attach failed for object %s: %s", name, e)
            else:
                item.setScale(st.get("scale", getattr(base_obj, "scale", 1.0)))
                item.setRotation(st.get("rotation", getattr(base_obj, "rotation", 0.0)))
                item.setZValue(st.get("z", getattr(base_obj, "z", 0)) + z_offset)
                item.setPos(
                    st.get("x", getattr(base_obj, "x", 0.0)),
                    st.get("y", getattr(base_obj, "y", 0.0)),
                )
                self.win.scene.addItem(item)
                self._onion_items.append(item)
        except (RuntimeError, OSError, KeyError) as e:
            logger.error("Onion object clone failed for %s: %s", name, e)

    # --- Implementation ---
    def _add_onion_for_frame(
        self, frame_index: int, opacity: float, z_offset: int = -200
    ) -> None:
        """Adds onion skins for a specific frame."""
        keyframes = self.win.scene_model.keyframes
        if not keyframes:
            return
        sorted_indices: List[int] = sorted(keyframes.keys())
        target_kf_index: Optional[int] = next(
            (i for i in reversed(sorted_indices) if i <= frame_index), None
        )
        if target_kf_index is None:
            return
        kf: Keyframe = keyframes[target_kf_index]

        clones_map: Dict[str, PuppetPiece] = {}
        for puppet_name, puppet in self.win.scene_model.puppets.items():
            clones = self._clone_puppet(puppet_name, puppet, kf, opacity, z_offset)
            for member_name, clone in clones.items():
                clones_map[f"{puppet_name}:{member_name}"] = clone

        for name, base_obj in self.win.scene_model.objects.items():
            self._clone_object(
                name, base_obj, kf, opacity, z_offset, clones_map, frame_index
            )
