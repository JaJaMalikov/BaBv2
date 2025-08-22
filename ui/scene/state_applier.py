"""Module for applying keyframe states to the scene."""

from __future__ import annotations

import logging
from typing import Dict, Optional, Any, List, Tuple

from PySide6.QtWidgets import QGraphicsItem

from core.scene_model import SceneObject, Keyframe
from core.puppet_piece import PuppetPiece
from .visibility_utils import update_piece_visibility


class StateApplier:
    """Apply model keyframe states to the current graphics items (puppets and objects)."""

    def __init__(self, win: "Any") -> None:
        """Store reference to main window-like object for scene access."""
        self.win = win

    def _lerp_angle(self, a: float, b: float, t: float) -> float:
        """Interpolate angles in degrees along the shortest arc.

        Keeps continuity when crossing 0/360 by wrapping the delta to [-180, 180].
        """
        # Normalize delta to [0, 360)
        delta = (b - a) % 360.0
        # Wrap to [-180, 180]
        if delta > 180.0:
            delta -= 360.0
        return a + delta * t

    def _set_object_parent(
        self,
        gi: QGraphicsItem,
        attachment: Optional[Tuple[str, str]],
        graphics_items: Dict[str, Any],
    ) -> None:
        """Ensure the graphics item's parent matches the attachment info."""
        if attachment:
            puppet_name, member_name = attachment
            parent_piece: Optional[PuppetPiece] = graphics_items.get(
                f"{puppet_name}:{member_name}"
            )
            if parent_piece is not None and gi.parentItem() is not parent_piece:
                gi.setParentItem(parent_piece)
        else:
            if gi.parentItem() is not None:
                gi.setParentItem(None)

    def _interpolate_object(
        self,
        gi: QGraphicsItem,
        prev_st: Dict[str, Any],
        next_st: Dict[str, Any],
        t: float,
        attachment: Optional[Tuple[str, str]],
        graphics_items: Dict[str, Any],
    ) -> None:
        """Interpolate transforms between two states for a graphics item."""
        self._set_object_parent(gi, attachment, graphics_items)
        px, py = float(prev_st.get("x", 0.0)), float(prev_st.get("y", 0.0))
        nx, ny = float(next_st.get("x", px)), float(next_st.get("y", py))
        gi.setPos(px + (nx - px) * t, py + (ny - py) * t)
        prot = float(prev_st.get("rotation", 0.0))
        nrot = float(next_st.get("rotation", prot))
        gi.setRotation(self._lerp_angle(prot, nrot, t))
        psc = float(prev_st.get("scale", 1.0))
        nsc = float(next_st.get("scale", psc))
        gi.setScale(psc + (nsc - psc) * t)
        gi.setZValue(int(prev_st.get("z", int(gi.zValue()))))

    def _apply_object_step(
        self,
        gi: QGraphicsItem,
        prev_st: Dict[str, Any],
        attachment: Optional[Tuple[str, str]],
        graphics_items: Dict[str, Any],
    ) -> None:
        """Apply a state without interpolation for a graphics item."""
        self._set_object_parent(gi, attachment, graphics_items)
        if attachment:
            gi.setPos(
                float(prev_st.get("x", 0.0)),
                float(prev_st.get("y", 0.0)),
            )
        else:
            gi.setPos(
                float(prev_st.get("x", gi.x())),
                float(prev_st.get("y", gi.y())),
            )
        gi.setRotation(float(prev_st.get("rotation", gi.rotation())))
        gi.setScale(float(prev_st.get("scale", gi.scale())))
        gi.setZValue(int(prev_st.get("z", int(gi.zValue()))))

    def apply_puppet_states(
        self,
        graphics_items: Dict[str, Any],
        keyframes: Dict[int, Keyframe],
        index: int,
    ) -> None:
        """Apply interpolated puppet transformations for the given frame index.

        Also applies per-slot variant visibility using the last known selection
        at or before the target frame (no interpolation between variants).
        """

        # Apply per-slot variant visibility first
        def _active_variants_for_puppet(puppet_name: str) -> Dict[str, str]:
            sel: Dict[str, str] = {}
            si: List[int] = sorted(keyframes.keys())
            last_kf_any: Optional[int] = next(
                (i for i in reversed(si) if i <= index), None
            )
            if last_kf_any is not None:
                kf = keyframes[last_kf_any]
                data = kf.puppets.get(puppet_name, {})
                vmap = data.get("_variants") if isinstance(data, dict) else None
                if isinstance(vmap, dict):
                    for k, v in vmap.items():
                        try:
                            sel[str(k)] = str(v)
                        except Exception:  # pylint: disable=broad-except
                            continue
            return sel

        for pname, puppet in self.win.scene_model.puppets.items():
            vconf = getattr(puppet, "variants", {})
            if not vconf:
                continue
            chosen = _active_variants_for_puppet(pname)
            for slot, candidates in vconf.items():
                target = chosen.get(slot, candidates[0] if candidates else None)
                for cand in candidates:
                    gi_key = f"{pname}:{cand}"
                    piece: Optional[PuppetPiece] = graphics_items.get(gi_key)  # type: ignore
                    if not piece:
                        continue
                    is_on = cand == target
                    update_piece_visibility(self.win, piece, is_on)

        sorted_indices: List[int] = sorted(keyframes.keys())
        prev_kf_index: int = next(
            (i for i in reversed(sorted_indices) if i <= index), -1
        )
        next_kf_index: int = next((i for i in sorted(sorted_indices) if i > index), -1)

        if (
            prev_kf_index != -1
            and next_kf_index != -1
            and prev_kf_index != next_kf_index
        ):
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
                    interp_rot: float = self._lerp_angle(
                        float(prev_state["rotation"]),
                        float(next_state["rotation"]),
                        ratio,
                    )
                    piece: PuppetPiece = graphics_items[f"{name}:{member_name}"]
                    piece.local_rotation = interp_rot
                    if not piece.parent_piece:
                        prev_pos: Tuple[float, float] = prev_state["pos"]
                        next_pos: Tuple[float, float] = next_state["pos"]
                        interp_x: float = (
                            prev_pos[0] + (next_pos[0] - prev_pos[0]) * ratio
                        )
                        interp_y: float = (
                            prev_pos[1] + (next_pos[1] - prev_pos[1]) * ratio
                        )
                        piece.setPos(interp_x, interp_y)
        else:
            target_kf_index: int = (
                prev_kf_index if prev_kf_index != -1 else next_kf_index
            )
            if target_kf_index == -1:
                return
            kf: Keyframe = keyframes[target_kf_index]
            # Only apply known puppet members; ignore meta-keys like '_variants'
            for name, puppet in self.win.scene_model.puppets.items():
                state = kf.puppets.get(name, {})
                for member_name in puppet.members:
                    member_state = state.get(member_name)
                    if not member_state:
                        continue
                    piece = graphics_items.get(f"{name}:{member_name}")
                    if not isinstance(piece, PuppetPiece):
                        continue
                    piece.local_rotation = float(
                        member_state.get("rotation", piece.local_rotation)
                    )
                    if not piece.parent_piece:
                        pos = member_state.get("pos")
                        if isinstance(pos, (list, tuple)) and len(pos) == 2:
                            piece.setPos(float(pos[0]), float(pos[1]))

        # Propagate transforms to children
        for name, puppet in self.win.scene_model.puppets.items():
            for root_member in puppet.get_root_members():
                root_piece: PuppetPiece = graphics_items[f"{name}:{root_member.name}"]
                root_piece.setRotation(root_piece.local_rotation)
                for child in root_piece.children:
                    child.update_transform_from_parent()

    def apply_object_states(
        self,
        graphics_items: Dict[str, Any],
        keyframes: Dict[int, Keyframe],
        index: int,
    ) -> None:
        """Apply object transformations and visibility for the given frame index."""

        def prev_and_next_state(
            obj_name: str,
        ) -> Tuple[
            Optional[int],
            Optional[Dict[str, Any]],
            Optional[int],
            Optional[Dict[str, Any]],
            bool,
        ]:
            """Return (prev_idx, prev_state, next_idx, next_state, visible) for an object.

            visible is False when the last keyframe at or before index omits the object
            (temporal deletion rule). In that case, other values may be None.
            """
            si: List[int] = sorted(keyframes.keys())
            last_kf_any: Optional[int] = next(
                (i for i in reversed(si) if i <= index), None
            )
            if (
                last_kf_any is not None
                and obj_name not in keyframes[last_kf_any].objects
            ):
                return None, None, None, None, False
            prev_idx: Optional[int] = next(
                (
                    i
                    for i in reversed(si)
                    if i <= index and obj_name in keyframes[i].objects
                ),
                None,
            )
            next_idx: Optional[int] = next(
                (i for i in si if i > index and obj_name in keyframes[i].objects), None
            )
            prev_state: Optional[Dict[str, Any]] = (
                keyframes[prev_idx].objects.get(obj_name)
                if prev_idx is not None
                else None
            )
            next_state: Optional[Dict[str, Any]] = (
                keyframes[next_idx].objects.get(obj_name)
                if next_idx is not None
                else None
            )
            return prev_idx, prev_state, next_idx, next_state, True

        updated: int = 0
        self.win._suspend_item_updates = True
        try:
            for name, base_obj in self.win.scene_model.objects.items():
                prev_idx, prev_st, next_idx, next_st, visible = prev_and_next_state(
                    name
                )
                gi: Optional[QGraphicsItem] = graphics_items.get(name)

                if not visible or prev_st is None:
                    if gi:
                        gi.setSelected(False)
                        gi.setVisible(False)
                    continue

                # Ensure graphics item exists
                if gi is None:
                    tmp: SceneObject = SceneObject(
                        name,
                        prev_st.get("obj_type", base_obj.obj_type),
                        prev_st.get("file_path", base_obj.file_path),
                        x=prev_st.get("x", base_obj.x),
                        y=prev_st.get("y", base_obj.y),
                        rotation=prev_st.get("rotation", base_obj.rotation),
                        scale=prev_st.get("scale", base_obj.scale),
                        z=prev_st.get("z", getattr(base_obj, "z", 0)),
                    )
                    # Use public SceneController API instead of private adapter method
                    self.win.scene_controller.add_object_graphics(tmp)
                    gi = graphics_items.get(name)

                if gi is None:
                    continue

                gi.setVisible(True)

                # Decide if we interpolate or step
                do_interp: bool = (
                    next_idx is not None
                    and prev_idx is not None
                    and next_idx != prev_idx
                    and next_idx > index
                )
                prev_att: Optional[Tuple[str, str]] = prev_st.get("attached_to")
                next_att: Optional[Tuple[str, str]] = (
                    next_st.get("attached_to") if next_st is not None else None
                )
                same_space: bool = prev_att == next_att

                if do_interp and same_space and next_st is not None:
                    t: float = (index - float(prev_idx)) / float(next_idx - prev_idx)
                    self._interpolate_object(
                        gi, prev_st, next_st, t, prev_att, graphics_items
                    )
                else:
                    self._apply_object_step(gi, prev_st, prev_att, graphics_items)

                updated += 1
        finally:
            self.win._suspend_item_updates = False
        logging.debug(f"Applied object states: {updated} updated/visible")
