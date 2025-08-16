"""Utilities for manipulating puppets within the scene view."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtSvg import QSvgRenderer

from core.puppet_model import Puppet, PuppetMember
from core.puppet_piece import PuppetPiece
from core.svg_loader import SvgLoader

if TYPE_CHECKING:
    from .scene_controller import MainWindowProtocol


class PuppetOps:
    """Operations related to puppet manipulation in the scene."""

    def __init__(self, win: MainWindowProtocol) -> None:
        """Initialize helper with a reference to the main window."""
        self.win = win

    def add_puppet(self, file_path: str, puppet_name: str) -> None:
        """Adds a puppet to the scene."""
        puppet: Puppet = Puppet()
        loader: SvgLoader = SvgLoader(file_path)
        renderer: QSvgRenderer = loader.renderer
        self.win.object_manager.renderers[puppet_name] = renderer
        puppet.build_from_svg(loader)
        self.win.scene_model.add_puppet(puppet_name, puppet)
        self.win.object_manager.puppet_scales[puppet_name] = 1.0
        self.win.object_manager.puppet_paths[puppet_name] = file_path
        self.win.object_manager.puppet_z_offsets[puppet_name] = 0
        self._add_puppet_graphics(puppet_name, puppet, file_path, renderer, loader)
        self.win.inspector_widget.refresh()

    def _add_puppet_graphics(
        self,
        puppet_name: str,
        puppet: Puppet,
        file_path: str,
        renderer: QSvgRenderer,
        loader: SvgLoader,
    ) -> None:
        """Adds the graphical representation of a puppet to the scene."""
        pieces: dict[str, PuppetPiece] = {}
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
            else:  # Root piece
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
                except (RuntimeError, TypeError):
                    logging.exception("Failed to set Z value for %s", name)

    def scale_puppet(self, puppet_name: str, ratio: float) -> None:
        """Scales a puppet by a given ratio."""
        puppet: Optional[Puppet] = self.win.scene_model.puppets.get(puppet_name)
        if not puppet:
            return
        for member_name in puppet.members:
            piece: Optional[PuppetPiece] = self.win.object_manager.graphics_items.get(
                f"{puppet_name}:{member_name}"
            )
            if not piece:
                continue
            piece.setScale(piece.scale() * ratio)
            if piece.parent_piece:
                piece.rel_to_parent = (
                    piece.rel_to_parent[0] * ratio,
                    piece.rel_to_parent[1] * ratio,
                )
        for root_member in puppet.get_root_members():
            if (
                root_piece := self.win.object_manager.graphics_items.get(
                    f"{puppet_name}:{root_member.name}"
                )
            ):
                for child in root_piece.children:
                    child.update_transform_from_parent()

    def delete_puppet(self, puppet_name: str) -> None:
        """Deletes a puppet from the scene."""
        if (puppet := self.win.scene_model.puppets.get(puppet_name)):
            for member_name in list(puppet.members.keys()):
                if (
                    piece := self.win.object_manager.graphics_items.pop(
                        f"{puppet_name}:{member_name}", None
                    )
                ):
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
        return self.win.object_manager.graphics_items.get(
            f"{puppet_name}:{roots[0].name}"
        )  # type: ignore

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
            piece: Optional[PuppetPiece] = self.win.object_manager.graphics_items.get(
                f"{puppet_name}:{member_name}"
            )
            if piece:
                try:
                    piece.setZValue(member.z_order + int(offset))
                except (RuntimeError, TypeError):
                    logging.exception("Failed to apply Z offset for %s", member_name)

    def unique_puppet_name(self, base: str) -> str:
        """Generates a unique name for a puppet."""
        name: str = base
        i: int = 1
        while name in self.win.scene_model.puppets:
            name = f"{base}_{i}"
            i += 1
        return name

    def set_rotation_handles_visible(self, visible: bool) -> None:
        """Show or hide rotation handles of all puppet pieces."""
        for item in self.win.object_manager.graphics_items.values():
            if isinstance(item, PuppetPiece):
                item.set_handle_visibility(visible)
        try:
            self.win.view.handles_btn.setChecked(visible)
        except (RuntimeError, AttributeError):
            logging.exception("Failed to sync handles button state")
