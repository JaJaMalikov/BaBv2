"""This module provides functions for handling scene import and export operations.

It includes functions for saving and loading scenes to/from JSON files, as well as
creating a blank scene.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFileDialog
from core.scene_validation import (
    validate_settings,
    validate_objects,
    validate_keyframes,
)

# Tests should use export_scene/import_scene directly; see ALLOW_FILE_DIALOGS below.
if TYPE_CHECKING:
    from ui.main_window import MainWindow


# Whether file dialogs are allowed. Tests should set this to False and call
# export_scene/import_scene directly. See docs/tasks.md Task 24.
ALLOW_FILE_DIALOGS: bool = True


def save_scene(win: "MainWindow") -> None:
    """Open a dialog to save the current scene to a JSON file.

    Notes for tests: avoid using this in headless mode. Instead call
    export_scene(win, path). To disable dialogs at runtime (e.g., tests), set
    ui.scene.scene_io.ALLOW_FILE_DIALOGS = False.
    """
    if not ALLOW_FILE_DIALOGS:
        logging.warning(
            "File dialogs disabled (ALLOW_FILE_DIALOGS=False). Use export_scene()."
        )
        return
    file_path: str
    file_path, _ = QFileDialog.getSaveFileName(
        win, "Sauvegarder la scène", "", "JSON Files (*.json)"
    )
    if file_path:
        export_scene(win, file_path)


def load_scene(win: "MainWindow") -> None:
    """Open a dialog to load a scene from a JSON file.

    Notes for tests: avoid using this in headless mode. Instead call
    import_scene(win, path). To disable dialogs at runtime (e.g., tests), set
    ui.scene.scene_io.ALLOW_FILE_DIALOGS = False.
    """
    if not ALLOW_FILE_DIALOGS:
        logging.warning(
            "File dialogs disabled (ALLOW_FILE_DIALOGS=False). Use import_scene()."
        )
        return
    file_path: str
    file_path, _ = QFileDialog.getOpenFileName(
        win, "Charger une scène", "", "JSON Files (*.json)"
    )
    if file_path:
        import_scene(win, file_path)


def export_scene(win: "MainWindow", file_path: str) -> None:
    """Exports the current scene state to a JSON file.

    Robustness notes (docs/tasks.md Task 9):
    - Ensure there is at least one keyframe (create at 0 if none).
    - Try to snapshot current frame only when graphics are likely ready and
      the method exists; treat failures as no-op with debug logging.
    """
    if not win.scene_model.keyframes:
        win.controller.add_keyframe(0)
    # Capture latest on-screen state into the current keyframe if it exists
    cur = win.scene_model.current_frame
    if cur in win.scene_model.keyframes:
        try:
            if hasattr(win, "object_controller") and hasattr(
                win.object_controller, "snapshot_current_frame"
            ):
                # Heuristic: skip if no graphics yet
                has_gfx = bool(getattr(win.object_view_adapter, "graphics_items", {}))
                if has_gfx:
                    win.object_controller.snapshot_current_frame()
        except (RuntimeError, TypeError, ValueError) as e:
            logging.debug("Snapshot on export ignored: %s", e)

    puppets_data: Dict[str, Dict[str, Any]] = {}
    for name, puppet in win.scene_model.puppets.items():
        root_members: List[Any] = puppet.get_root_members()
        if not root_members:
            continue
        root_piece: Optional[Any] = win.object_manager.graphics_items.get(
            f"{name}:{root_members[0].name}"
        )
        if root_piece:
            puppets_data[name] = {
                "path": win.object_manager.puppet_paths.get(name),
                "scale": win.object_manager.puppet_scales.get(name, 1.0),
                "position": [root_piece.x(), root_piece.y()],
                "rotation": win.scene_controller.get_puppet_rotation(name),
                "z_offset": win.object_manager.puppet_z_offsets.get(name, 0),
            }

    data: Dict[str, Any] = win.scene_model.to_dict()
    data["puppets_data"] = puppets_data

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logging.info("Scene saved to %s", file_path)
    except (OSError, TypeError) as e:
        logging.error("Error saving scene '%s': %s", file_path, e)


def import_scene(win: MainWindow, file_path: str) -> None:
    """Imports a scene from a JSON file, rebuilding the entire scene state."""
    try:
        # Chargement du fichier JSON (exceptions ciblées)
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Validate structure before applying to live model
        if not (
            validate_settings(data.get("settings"))
            and validate_objects(data.get("objects"))
            and validate_keyframes(data.get("keyframes"))
        ):
            logging.error("Scene import validation failed for '%s'", file_path)
            create_blank_scene(win, add_default_puppet=False)
            return
        create_blank_scene(win, add_default_puppet=False)
        win.scene_model.from_dict(data)
        puppets_data = data.get("puppets_data", {})
        for name, p_data in puppets_data.items():
            puppet_path = p_data.get("path")
            if puppet_path and Path(puppet_path).exists():
                win.scene_controller.add_puppet(puppet_path, name)
                scale = p_data.get("scale", 1.0)
                if scale != 1.0:
                    win.scene_controller.scale_puppet(name, scale)
                    win.object_manager.puppet_scales[name] = scale
                pos = p_data.get("position")
                root_members = win.scene_model.puppets[name].get_root_members()
                if root_members:
                    root_piece = win.object_manager.graphics_items.get(
                        f"{name}:{root_members[0].name}"
                    )
                    if root_piece and pos:
                        root_piece.setPos(pos[0], pos[1])
                # Optional rotation and z offset
                try:
                    rot = float(p_data.get("rotation", 0.0))
                    if abs(rot) > 1e-9:
                        win.scene_controller.set_puppet_rotation(name, rot)
                except (TypeError, ValueError):
                    logging.exception("Invalid rotation value in puppets_data")
                try:
                    zoff = int(p_data.get("z_offset", 0))
                    if zoff:
                        win.scene_controller.set_puppet_z_offset(name, zoff)
                except (TypeError, ValueError):
                    logging.exception("Invalid z_offset value in puppets_data")

        for obj in win.scene_model.objects.values():
            try:
                win.scene_controller.add_object_graphics(obj)
            except RuntimeError as e:
                logging.error(
                    "Failed to create graphics for '%s': %s",
                    getattr(obj, "name", "?"),
                    e,
                )

        win.timeline_widget.clear_keyframes()
        for kf_index in win.scene_model.keyframes:
            win.timeline_widget.add_keyframe_marker(kf_index)

        win.playback_handler.update_timeline_ui_from_model()
        win.scene.setSceneRect(
            0, 0, win.scene_model.scene_width, win.scene_model.scene_height
        )
        try:
            win.scene_controller.update_background()
        except RuntimeError:
            logging.exception(
                "Scene controller background update failed, using fallback"
            )
            win._update_background()
        # Consolidate visual updates to avoid redundant work: set the frame and
        # apply the model state once the event loop is idle.
        QTimer.singleShot(
            0,
            lambda: (
                win.timeline_widget.set_current_frame(
                    win.scene_model.current_frame or win.scene_model.start_frame
                ),
                win.inspector_widget.refresh(),
                win.controller.update_scene_from_model(),
            ),
        )

    except json.JSONDecodeError as e:
        logging.error("Invalid JSON in scene file '%s': %s", file_path, e)
        create_blank_scene(win, add_default_puppet=False)
    except OSError as e:
        logging.error("File IO error while loading scene '%s': %s", file_path, e)
        create_blank_scene(win, add_default_puppet=False)
    except (RuntimeError, AttributeError, ValueError):
        # Log full traceback for unexpected errors while applying model/state
        logging.exception("Model/state error while loading scene '%s'", file_path)
        create_blank_scene(win, add_default_puppet=False)


def create_blank_scene(win: "MainWindow", add_default_puppet: bool = False) -> None:
    """Clears the scene and optionally adds a default puppet."""
    for name in list(win.scene_model.puppets.keys()):
        win.scene_controller.delete_puppet(name)
    for name in list(win.scene_model.objects.keys()):
        win.scene_controller.delete_object(name)
    win.object_manager.renderers.clear()
    win.object_manager.graphics_items.clear()
    win.scene_model.keyframes.clear()
    win.timeline_widget.clear_keyframes()
    if add_default_puppet:
        win.scene_controller.add_puppet("assets/pantins/manu.svg", "manu")
    win.playback_handler.update_timeline_ui_from_model()
    win.inspector_widget.refresh()
