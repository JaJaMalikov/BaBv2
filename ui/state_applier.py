from __future__ import annotations

import logging
from typing import Dict, Optional, Any, List, Tuple

from PySide6.QtWidgets import QGraphicsItem

from core.scene_model import SceneObject, Keyframe
from core.puppet_piece import PuppetPiece


class StateApplier:
    """Apply model keyframe states to the current graphics items (puppets and objects)."""

    def __init__(self, win: 'Any') -> None:
        self.win = win

    def apply_puppet_states(self, graphics_items: Dict[str, Any], keyframes: Dict[int, Keyframe], index: int) -> None:
        sorted_indices: List[int] = sorted(keyframes.keys())
        prev_kf_index: int = next((i for i in reversed(sorted_indices) if i <= index), -1)
        next_kf_index: int = next((i for i in sorted(sorted_indices) if i > index), -1)

        if prev_kf_index != -1 and next_kf_index != -1 and prev_kf_index != next_kf_index:
            prev_kf: Keyframe = keyframes[prev_kf_index]
            next_kf: Keyframe = keyframes[next_kf_index]
            ratio: float = (index - prev_kf_index) / (next_kf_index - prev_kf_index)
            for name, puppet in self.win.scene_model.puppets.items():
                prev_pose: Dict[str, Dict[str, Any]] = prev_kf.puppets.get(name, {})
                next_pose: Dict[str, Dict[str, Any]] = next_kf.puppets.get(name, {})
                for member_name in puppet.members:
                    prev_state: Optional[Dict[str, Any]] = prev_pose.get(member_name)
                    next_state: Optional[Dict[str, Any]] = next_pose.get(member_name)
                    if not prev_state or not next_state:
                        continue
                    interp_rot: float = prev_state['rotation'] + (next_state['rotation'] - prev_state['rotation']) * ratio
                    piece: PuppetPiece = graphics_items[f"{name}:{member_name}"]
                    piece.local_rotation = interp_rot
                    if not piece.parent_piece:
                        prev_pos: Tuple[float, float] = prev_state['pos']
                        next_pos: Tuple[float, float] = next_state['pos']
                        interp_x: float = prev_pos[0] + (next_pos[0] - prev_pos[0]) * ratio
                        interp_y: float = prev_pos[1] + (next_pos[1] - prev_pos[1]) * ratio
                        piece.setPos(interp_x, interp_y)
        else:
            target_kf_index: int = prev_kf_index if prev_kf_index != -1 else next_kf_index
            if target_kf_index == -1:
                return
            kf: Keyframe = keyframes[target_kf_index]
            for name, state in kf.puppets.items():
                for member, member_state in state.items():
                    piece: PuppetPiece = graphics_items[f"{name}:{member}"]
                    piece.local_rotation = member_state['rotation']
                    if not piece.parent_piece:
                        piece.setPos(*member_state['pos'])

        # Propagate transforms to children
        for name, puppet in self.win.scene_model.puppets.items():
            for root_member in puppet.get_root_members():
                root_piece: PuppetPiece = graphics_items[f"{name}:{root_member.name}"]
                root_piece.setRotation(root_piece.local_rotation)
                for child in root_piece.children:
                    child.update_transform_from_parent()

    def apply_object_states(self, graphics_items: Dict[str, Any], keyframes: Dict[int, Keyframe], index: int) -> None:
        def state_for(obj_name: str) -> Optional[Dict[str, Any]]:
            si: List[int] = sorted(keyframes.keys())
            last_kf: Optional[int] = next((i for i in reversed(si) if i <= index), None)
            if last_kf is not None and obj_name not in keyframes[last_kf].objects:
                return None
            prev_including: Optional[int] = next((i for i in reversed(si) if i <= index and obj_name in keyframes[i].objects), None)
            if prev_including is None:
                return None
            return keyframes[prev_including].objects.get(obj_name)

        updated: int = 0
        self.win._suspend_item_updates = True
        try:
            for name, base_obj in self.win.scene_model.objects.items():
                st: Optional[Dict[str, Any]] = state_for(name)
                gi: Optional[QGraphicsItem] = graphics_items.get(name)
                if st is None:
                    if gi:
                        gi.setSelected(False)
                        gi.setVisible(False)
                    continue
                if gi is None:
                    tmp: SceneObject = SceneObject(
                        name,
                        st.get('obj_type', base_obj.obj_type),
                        st.get('file_path', base_obj.file_path),
                        x=st.get('x', base_obj.x),
                        y=st.get('y', base_obj.y),
                        rotation=st.get('rotation', base_obj.rotation),
                        scale=st.get('scale', base_obj.scale),
                        z=st.get('z', getattr(base_obj, 'z', 0))
                    )
                    self.win.object_manager._add_object_graphics(tmp)
                    gi = graphics_items.get(name)
                if gi:
                    gi.setVisible(True)
                    attached: Optional[Tuple[str, str]] = st.get('attached_to', None)
                    if attached:
                        puppet_name, member_name = attached
                        parent_piece: Optional[PuppetPiece] = graphics_items.get(f"{puppet_name}:{member_name}")
                        # Always set the parent first, then apply the saved local transform
                        if parent_piece is not None and gi.parentItem() is not parent_piece:
                            gi.setParentItem(parent_piece)
                        # Apply local coordinates from state (default to 0,0)
                        gi.setPos(float(st.get('x', 0.0)), float(st.get('y', 0.0)))
                    else:
                        # Ensure the item is in scene coordinates
                        if gi.parentItem() is not None:
                            gi.setParentItem(None)
                        gi.setPos(float(st.get('x', gi.x())), float(st.get('y', gi.y())))
                    gi.setRotation(float(st.get('rotation', gi.rotation())))
                    gi.setScale(float(st.get('scale', gi.scale())))
                    gi.setZValue(int(st.get('z', int(gi.zValue()))))
                    updated += 1
        finally:
            self.win._suspend_item_updates = False
        logging.debug(f"Applied object states: {updated} updated/visible")

