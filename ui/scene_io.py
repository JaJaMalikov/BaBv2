from __future__ import annotations
import json
from pathlib import Path

from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import QTimer

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from .main_window import MainWindow

def save_scene(win: 'MainWindow') -> None:
    """Opens a dialog to save the current scene to a JSON file."""
    filePath: str
    filePath, _ = QFileDialog.getSaveFileName(win, "Sauvegarder la scène", "", "JSON Files (*.json)")
    if filePath:
        export_scene(win, filePath)

def load_scene(win: 'MainWindow') -> None:
    """Opens a dialog to load a scene from a JSON file."""
    filePath: str
    filePath, _ = QFileDialog.getOpenFileName(win, "Charger une scène", "", "JSON Files (*.json)")
    if filePath:
        import_scene(win, filePath)

import logging # Added for error handling

def export_scene(win: 'MainWindow', file_path: str) -> None:
    """Exports the current scene state to a JSON file."""
    if not win.scene_model.keyframes:
        win.add_keyframe(0)

    puppets_data: Dict[str, Dict[str, Any]] = {}
    for name, puppet in win.scene_model.puppets.items():
        root_members: List[Any] = puppet.get_root_members()
        if not root_members:
            continue
        root_piece: Optional[Any] = win.object_manager.graphics_items.get(f"{name}:{root_members[0].name}")
        if root_piece:
            puppets_data[name] = {
                "path": win.object_manager.puppet_paths.get(name),
                "scale": win.object_manager.puppet_scales.get(name, 1.0),
                "position": [root_piece.x(), root_piece.y()],
            }

    data: Dict[str, Any] = win.scene_model.to_dict()
    data["puppets_data"] = puppets_data

    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        logging.info(f"Scene saved to {file_path}")
    except (IOError, TypeError) as e:
        logging.error(f"Error saving scene: {e}")

def import_scene(win: MainWindow, file_path: str):
    """Imports a scene from a JSON file, rebuilding the entire scene state."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        create_blank_scene(win, add_default_puppet=False)

        win.scene_model.from_dict(data)

        puppets_data = data.get("puppets_data", {})
        for name, p_data in puppets_data.items():
            puppet_path = p_data.get("path")
            if puppet_path and Path(puppet_path).exists():
                win.object_manager.add_puppet(puppet_path, name)
                scale = p_data.get("scale", 1.0)
                if scale != 1.0:
                    win.object_manager.scale_puppet(name, scale)
                    win.object_manager.puppet_scales[name] = scale
                
                pos = p_data.get("position")
                root_members = win.scene_model.puppets[name].get_root_members()
                if root_members:
                    root_piece = win.object_manager.graphics_items.get(f"{name}:{root_members[0].name}")
                    if root_piece and pos:
                        root_piece.setPos(pos[0], pos[1])

        for obj in win.scene_model.objects.values():
            try:
                win.object_manager._add_object_graphics(obj)
            except Exception as e:
                print(f"Failed to create graphics for '{obj.name}': {e}")

        win.timeline_widget.clear_keyframes()
        for kf_index in win.scene_model.keyframes:
            win.timeline_widget.add_keyframe_marker(kf_index)
        
        win.playback_handler.update_timeline_ui_from_model()
        win.scene.setSceneRect(0, 0, win.scene_model.scene_width, win.scene_model.scene_height)
        win._update_background()
        win.timeline_widget.set_current_frame(win.scene_model.start_frame)
        win.inspector_widget.refresh()

        QTimer.singleShot(0, lambda: win.timeline_widget.set_current_frame(win.scene_model.current_frame or win.scene_model.start_frame))

    except Exception as e:
        print(f"Failed to load scene '{file_path}': {e}")
        create_blank_scene(win, add_default_puppet=False)

def create_blank_scene(win: 'MainWindow', add_default_puppet: bool = False) -> None:
    """Clears the scene and optionally adds a default puppet."""
    for name in list(win.scene_model.puppets.keys()): win.object_manager.delete_puppet(name)
    for name in list(win.scene_model.objects.keys()): win.object_manager.delete_object(name)
    win.object_manager.renderers.clear()
    win.object_manager.graphics_items.clear()
    win.scene_model.keyframes.clear()
    win.timeline_widget.clear_keyframes()
    if add_default_puppet:
        win.object_manager.add_puppet("assets/pantins/manu.svg", "manu")
    win.playback_handler.update_timeline_ui_from_model()
    win.inspector_widget.refresh()
