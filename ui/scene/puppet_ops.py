"""Utilities for manipulating puppets within the scene view.

DEPRECATION NOTICE (docs/tasks.md §23):
- This module performs direct access to `win.scene_model` and
  `win.object_manager.graphics_items`. These patterns are being migrated to a
  controller/facade API and selection model. New code should avoid adding more
  direct accesses and instead route via controllers/state_applier.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional
from pathlib import Path
import json

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtSvg import QSvgRenderer

from core.puppet_model import Puppet, PuppetMember, normalize_variants
from core.naming import unique_name, puppet_member_key
from ui.scene.puppet_piece import PuppetPiece
from core.svg_loader import SvgLoader

# Named constants
DEFAULT_PUPPET_Z_OFFSET = 0
DUPLICATE_OFFSET = 10

if TYPE_CHECKING:
    from .scene_controller import MainWindowProtocol
    from controllers.scene_service import SceneService


class PuppetOps:
    """Operations related to puppet manipulation in the scene."""

    def __init__(self, win: MainWindowProtocol, scene_service: SceneService) -> None:
        """Initialize helper with a reference to la fenêtre et au service."""
        self.win = win
        self.scene_service = scene_service
        # Keep references to async watchers to avoid GC before completion
        self._async_watchers: list[object] = []

    def add_puppet(self, file_path: str, puppet_name: str) -> None:
        """Adds a puppet to the scene.

        Optionally offloads SVG XML parsing to a background thread when the
        setting ``performance/async_svg_load`` is enabled in QSettings. The
        rest of the work (Qt renderer creation and graphics items) stays on the UI thread.
        """
        # Check async setting (default False to keep tests deterministic)
        try:
            from PySide6.QtCore import QSettings

            s = QSettings("JaJa", "Macronotron")
            use_async = bool(s.value("performance/async_svg_load", False))
        except Exception:
            use_async = False

        if use_async:
            try:
                # Use QtConcurrent to parse XML off the UI thread and signal completion
                from PySide6.QtConcurrent import run as _qt_run  # type: ignore
                from PySide6.QtCore import QFutureWatcher
                import xml.etree.ElementTree as ET

                def _worker_parse(path: str):
                    tree = ET.parse(path)
                    # Sidecar variants (optional)
                    raw_variants = None
                    svg_path = Path(path)
                    for sidecar in (
                        svg_path.with_suffix(".json"),
                        svg_path.with_name(f"conf_{svg_path.stem}.json"),
                    ):
                        try:
                            if sidecar.exists():
                                with sidecar.open("r", encoding="utf-8") as fh:
                                    data = json.load(fh)
                                if isinstance(data, dict):
                                    raw_variants = data.get("variants", {})
                                break
                        except (OSError, ValueError):
                            # Swallow here; will be logged on UI thread if needed
                            raw_variants = None
                    return tree, raw_variants

                future = _qt_run(_worker_parse, file_path)
                watcher: QFutureWatcher = QFutureWatcher()
                watcher.setFuture(future)
                # keep a reference until finished
                self._async_watchers.append(watcher)

                def _finish():
                    try:
                        tree, raw_variants = future.result()
                    except Exception:
                        logging.exception("Async SVG parse failed for %s", file_path)
                        return
                    # Continue on UI thread
                    puppet: Puppet = Puppet()
                    try:
                        if isinstance(raw_variants, dict):
                            vmap, vz = normalize_variants(raw_variants)
                            puppet.variants = vmap
                            puppet.variant_z = vz
                    except Exception:
                        logging.exception("Applying sidecar variants failed for %s", file_path)
                    try:
                        loader: SvgLoader = SvgLoader.from_parsed(file_path, tree)
                        renderer: QSvgRenderer = QSvgRenderer(file_path)
                        loader.attach_renderer(renderer)
                        self.win.object_manager.renderers[puppet_name] = renderer
                        puppet.build_from_svg(loader)
                        self.scene_service.add_puppet(puppet_name, puppet)
                        self.win.object_manager.puppet_scales[puppet_name] = 1.0
                        self.win.object_manager.puppet_paths[puppet_name] = file_path
                        self.win.object_manager.puppet_z_offsets[puppet_name] = (
                            DEFAULT_PUPPET_Z_OFFSET
                        )
                        self._add_puppet_graphics(puppet_name, puppet, file_path, renderer, loader)
                        self.win.inspector_widget.refresh()
                    except Exception:
                        logging.exception("Failed to finalize puppet load for %s", file_path)

                watcher.finished.connect(_finish)
                return
            except Exception:
                # Fallback to synchronous path if QtConcurrent or watcher unavailable
                logging.debug("QtConcurrent unavailable; falling back to sync SVG load")

        # Synchronous path (default)
        puppet: Puppet = Puppet()
        loader: SvgLoader = SvgLoader(file_path)
        renderer: QSvgRenderer = QSvgRenderer(file_path)
        loader.attach_renderer(renderer)
        self.win.object_manager.renderers[puppet_name] = renderer
        # Optionnel: charger un fichier JSON de configuration à côté du SVG
        # pour définir des variantes spécifiques au pantin (sans toucher au fichier global).
        try:
            svg_path = Path(file_path)
            candidates = [
                svg_path.with_suffix(".json"),
                svg_path.with_name(f"conf_{svg_path.stem}.json"),
            ]
            for sidecar in candidates:
                if sidecar.exists():
                    with sidecar.open("r", encoding="utf-8") as fh:
                        data = json.load(fh)
                    if isinstance(data, dict):
                        vmap, vz = normalize_variants(data.get("variants", {}))
                        puppet.variants = vmap
                        puppet.variant_z = vz
                    break
        except (OSError, ValueError):
            logging.exception("Sidecar variants loading failed for %s", file_path)
        puppet.build_from_svg(loader)
        self.scene_service.add_puppet(puppet_name, puppet)
        self.win.object_manager.puppet_scales[puppet_name] = 1.0
        self.win.object_manager.puppet_paths[puppet_name] = file_path
        self.win.object_manager.puppet_z_offsets[puppet_name] = DEFAULT_PUPPET_Z_OFFSET
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
        """Add the graphical representation of a puppet to the scene."""
        pieces: dict[str, PuppetPiece] = {}
        for name, member in puppet.members.items():
            offset_x, offset_y = loader.get_group_offset(name) or (0.0, 0.0)
            pivot_x, pivot_y = member.pivot[0] - offset_x, member.pivot[1] - offset_y
            piece: PuppetPiece = PuppetPiece(file_path, name, pivot_x, pivot_y, renderer)
            piece.setZValue(member.z_order)
            pieces[name] = piece
            self.win.object_manager.graphics_items[puppet_member_key(puppet_name, name)] = piece

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

        # Apply per-variant base Z override (absolute) if defined
        try:
            for name, piece in pieces.items():
                member = puppet.members[name]
                base_z = int(puppet.variant_z.get(name, member.z_order))
                piece.setZValue(base_z)
        except (ValueError, TypeError, RuntimeError, KeyError, AttributeError):
            logging.exception("Failed to apply base Z for variants")

        # Apply z offset if any (default 0), respecting per-variant base Z
        zoff: int = self.win.object_manager.puppet_z_offsets.get(puppet_name, 0)
        for name, piece in pieces.items():
            member = puppet.members[name]
            try:
                base_z = int(puppet.variant_z.get(name, member.z_order))
                piece.setZValue(base_z + zoff)
            except (RuntimeError, TypeError):
                logging.exception("Failed to set Z value for %s", name)

        # Final pass: align puppet bottom to scene bottom while keeping horizontal center.
        try:
            self._align_puppet_bottom(puppet_name, pieces)
        except Exception:  # pylint: disable=broad-except
            logging.exception("Failed to align puppet bottom for %s", puppet_name)

        # Apply initial variants visibility: default to first variant per slot
        if getattr(puppet, "variants", None):
            try:
                for slot, candidates in puppet.variants.items():
                    if not candidates:
                        continue
                    default_var = candidates[0]
                    for cand in candidates:
                        gi_key = puppet_member_key(puppet_name, cand)
                        piece = self.win.object_manager.graphics_items.get(gi_key)
                        if not piece:
                            continue
                        is_on = cand == default_var
                        from .visibility_utils import update_piece_visibility

                        update_piece_visibility(self.win, piece, is_on)
            except Exception:  # pylint: disable=broad-except
                logging.exception("Failed to apply initial variants visibility")

    def scale_puppet(self, puppet_name: str, ratio: float) -> None:
        """Scales a puppet by a given ratio."""
        puppet: Optional[Puppet] = self.win.scene_model.puppets.get(puppet_name)
        if not puppet:
            return
        for member_name in puppet.members:
            piece: Optional[PuppetPiece] = self.win.object_manager.graphics_items.get(
                puppet_member_key(puppet_name, member_name)
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
            if root_piece := self.win.object_manager.graphics_items.get(
                puppet_member_key(puppet_name, root_member.name)
            ):
                for child in root_piece.children:
                    child.update_transform_from_parent()

    def delete_puppet(self, puppet_name: str) -> None:
        """Deletes a puppet from the scene."""
        if puppet := self.win.scene_model.puppets.get(puppet_name):
            for member_name in list(puppet.members.keys()):
                if piece := self.win.object_manager.graphics_items.pop(
                    puppet_member_key(puppet_name, member_name), None
                ):
                    self.win.scene.removeItem(piece)
                    if piece.pivot_handle:
                        self.win.scene.removeItem(piece.pivot_handle)
                    if piece.rotation_handle:
                        self.win.scene.removeItem(piece.rotation_handle)
            self.scene_service.remove_puppet(puppet_name)
            self.win.object_manager.puppet_scales.pop(puppet_name, None)
            self.win.object_manager.puppet_paths.pop(puppet_name, None)
            self.win.object_manager.puppet_z_offsets.pop(puppet_name, None)

    def duplicate_puppet(self, puppet_name: str) -> None:
        """Duplicates a puppet with deep-copy semantics.

        Copies visual state (root position with small offset, rotation), scale,
        z-offset, and currently active variants.
        """
        path: Optional[str] = self.win.object_manager.puppet_paths.get(puppet_name)
        if not path:
            return
        base: str = puppet_name
        i: int = 1
        new_name: str = f"{base}_{i}"
        while new_name in self.win.scene_model.puppets:
            i += 1
            new_name = f"{base}_{i}"
        # Create the new puppet
        self.add_puppet(path, new_name)

        # Copy scale first
        scale: float = self.win.object_manager.puppet_scales.get(puppet_name, 1.0)
        if scale != 1.0:
            self.win.object_manager.puppet_scales[new_name] = scale
            self.scale_puppet(new_name, scale)

        # Copy z-offset
        zoff: int = self.win.object_manager.puppet_z_offsets.get(puppet_name, 0)
        if zoff:
            self.set_puppet_z_offset(new_name, zoff)

        # Copy root position and rotation (offset slightly to avoid exact overlap)
        try:
            src_root = self._puppet_root_piece(puppet_name)
            dst_root = self._puppet_root_piece(new_name)
            if src_root and dst_root:
                new_x = src_root.x() + float(DUPLICATE_OFFSET)
                new_y = src_root.y() + float(DUPLICATE_OFFSET)
                dst_root.setPos(new_x, new_y)
                # Copy rotation
                angle = self.get_puppet_rotation(puppet_name)
                self.set_puppet_rotation(new_name, angle)
                # Propagate to children
                for child in dst_root.children:
                    child.update_transform_from_parent()
        except Exception:  # pylint: disable=broad-except
            logging.exception("Failed to copy transform for duplicated puppet %s", new_name)

        # Copy active variants (visuals + persist in current frame)
        try:
            src_puppet = self.win.scene_model.puppets.get(puppet_name)
            if src_puppet and getattr(src_puppet, "variants", None):
                for slot, _cands in src_puppet.variants.items():
                    active = self.get_active_variant(puppet_name, slot)
                    if active:
                        # Update visuals
                        self.set_member_variant(new_name, slot, active)
                        # Persist in model at current frame
                        self.scene_service.set_member_variant(new_name, slot, active)
        except Exception:  # pylint: disable=broad-except
            logging.exception("Failed to copy variants for duplicated puppet %s", new_name)

    def _puppet_root_piece(self, puppet_name: str) -> Optional[PuppetPiece]:
        """Returns the root piece of a puppet."""
        puppet: Optional[Puppet] = self.win.scene_model.puppets.get(puppet_name)
        if not puppet:
            return None
        roots = puppet.get_root_members()
        if not roots:
            return None
        return self.win.object_manager.graphics_items.get(
            puppet_member_key(puppet_name, roots[0].name)
        )  # type: ignore

    def set_puppet_root_pos(self, puppet_name: str, pos: QPointF) -> None:
        """Set the root position of a puppet and update children transforms.

        This centralizes root placement logic to avoid direct graphics access from
        other UI modules (docs/tasks.md §7).
        """
        root = self._puppet_root_piece(puppet_name)
        if not isinstance(root, PuppetPiece):
            return
        try:
            root.setPos(float(pos.x()), float(pos.y()))
            for child in root.children:
                child.update_transform_from_parent()
        except Exception:  # pylint: disable=broad-except
            logging.exception("Failed to set root position for puppet %s", puppet_name)

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
                puppet_member_key(puppet_name, member_name)
            )
            if piece:
                try:
                    base_z = int(puppet.variant_z.get(member_name, member.z_order))
                    piece.setZValue(base_z + int(offset))
                except (RuntimeError, TypeError):
                    logging.exception("Failed to apply Z offset for %s", member_name)

    def unique_puppet_name(self, base: str) -> str:
        """Generates a unique name for a puppet."""
        return unique_name(base, self.win.scene_model.puppets.keys())

    def set_rotation_handles_visible(self, visible: bool) -> None:
        """Show or hide rotation handles of all puppet pieces."""
        for item in self.win.object_manager.graphics_items.values():
            if isinstance(item, PuppetPiece):
                item.set_handle_visibility(visible)
        try:
            self.win.view.handles_btn.setChecked(visible)
        except (RuntimeError, AttributeError):
            logging.exception("Failed to sync handles button state")

    # --- Variants ---------------------------------------------------------
    def set_member_variant(self, puppet_name: str, slot: str, variant_name: str) -> None:
        """Set the active variant for a logical slot on a puppet and update visibility."""
        puppet: Optional[Puppet] = self.win.scene_model.puppets.get(puppet_name)
        if not puppet:
            return
        candidates = list(getattr(puppet, "variants", {}).get(slot, []))
        if not candidates:
            return
        if variant_name not in candidates:
            # If invalid, fallback to first
            variant_name = candidates[0]
        for cand in candidates:
            gi_key = puppet_member_key(puppet_name, cand)
            piece = self.win.object_manager.graphics_items.get(gi_key)
            if not piece:
                continue
            is_on = cand == variant_name
            try:
                from .visibility_utils import update_piece_visibility

                update_piece_visibility(self.win, piece, is_on)
            except Exception:
                logging.debug("Failed to update visibility for variant %s", gi_key)

    def get_active_variant(self, puppet_name: str, slot: str) -> Optional[str]:
        """Return current active variant name for a slot by inspecting visibility."""
        puppet: Optional[Puppet] = self.win.scene_model.puppets.get(puppet_name)
        if not puppet:
            return None
        candidates = getattr(puppet, "variants", {}).get(slot, [])
        for cand in candidates:
            piece = self.win.object_manager.graphics_items.get(puppet_member_key(puppet_name, cand))
            try:
                if piece and piece.isVisible():
                    return cand
            except RuntimeError:
                continue
        return candidates[0] if candidates else None

    # --- Helpers ---------------------------------------------------------
    def _align_puppet_bottom(self, puppet_name: str, pieces: dict[str, PuppetPiece]) -> None:
        """Align the union bbox of visible puppet pieces to scene bottom, keep X center.

        Computes the union of sceneBoundingRect for all visible pieces of the puppet
        and shifts the root piece vertically so the union.bottom matches scene.bottom.
        """
        root = self._puppet_root_piece(puppet_name)
        if not isinstance(root, PuppetPiece):
            return
        # Union of visible pieces
        union_rect = None
        for p in pieces.values():
            try:
                if not p.isVisible():
                    continue
                r = p.sceneBoundingRect()
                union_rect = r if union_rect is None else union_rect.united(r)
            except RuntimeError:
                continue
        if union_rect is None:
            return
        scene_bottom = self.win.scene.sceneRect().bottom()
        delta_y = scene_bottom - union_rect.bottom()
        if abs(delta_y) < 0.5:
            return
        new_x = root.x()
        new_y = root.y() + delta_y
        root.setPos(new_x, new_y)
        # Propagate to children for correctness
        for child in root.children:
            child.update_transform_from_parent()
