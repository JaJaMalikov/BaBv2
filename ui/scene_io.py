from __future__ import annotations
import json
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import QTimer

from core.scene_model import SceneObject

if TYPE_CHECKING:
    from .main_window import MainWindow

def save_scene(win: MainWindow):
    """Opens a dialog to save the current scene to a JSON file."""
    filePath, _ = QFileDialog.getSaveFileName(win, "Sauvegarder la scène", "", "JSON Files (*.json)")
    if filePath:
        export_scene(win, filePath)

def load_scene(win: MainWindow):
    """Opens a dialog to load a scene from a JSON file."""
    filePath, _ = QFileDialog.getOpenFileName(win, "Charger une scène", "", "JSON Files (*.json)")
    if filePath:
        import_scene(win, filePath)

def export_scene(win: MainWindow, file_path: str):
    """Exports the current scene state to a JSON file."""
    if not win.scene_model.keyframes:
        win.add_keyframe(0)

    puppets_data = {}
    for name, puppet in win.scene_model.puppets.items():
        root_members = puppet.get_root_members()
        if not root_members: continue
        root_piece = win.object_manager.graphics_items.get(f"{name}:{root_members[0].name}")
        if root_piece:
            puppets_data[name] = {
                "path": win.object_manager.puppet_paths.get(name),
                "scale": win.object_manager.puppet_scales.get(name, 1.0),
                "position": [root_piece.x(), root_piece.y()]
            }

    data = {
        "settings": {
            "start_frame": win.scene_model.start_frame,
            "end_frame": win.scene_model.end_frame,
            "fps": win.scene_model.fps,
            "scene_width": win.scene_model.scene_width,
            "scene_height": win.scene_model.scene_height,
            "background_path": win.scene_model.background_path
        },
        "puppets_data": puppets_data,
        "objects": {k: v.to_dict() for k, v in win.scene_model.objects.items()},
        "keyframes": {
            k: {"objects": v.objects, "puppets": v.puppets}
            for k, v in win.scene_model.keyframes.items()
        }
    }
    
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Scene saved to {file_path}")
    except (IOError, TypeError) as e:
        print(f"Error saving scene: {e}")

def import_scene(win: MainWindow, file_path: str):
    """Imports a scene from a JSON file, rebuilding the entire scene state."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        create_blank_scene(win, add_default_puppet=False)

        settings = data.get("settings", {})
        win.scene_model.start_frame = settings.get("start_frame", 0)
        win.scene_model.end_frame = settings.get("end_frame", 100)
        win.scene_model.fps = settings.get("fps", 24)
        win.scene_model.scene_width = settings.get("scene_width", 1920)
        win.scene_model.scene_height = settings.get("scene_height", 1080)
        win.scene_model.background_path = settings.get("background_path")

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

        win.scene_model.objects.clear()
        objects_data = data.get("objects", {})
        for name, obj_data in objects_data.items():
            try:
                obj_data["name"] = name
                obj = SceneObject.from_dict(obj_data)
                win.scene_model.add_object(obj)
            except Exception as e:
                print(f"Failed to load object '{name}': {e}")

        win.scene_model.keyframes.clear()
        keyframes_data = data.get("keyframes", {})
        for frame_idx, kf_data in keyframes_data.items():
            kf = win.scene_model.add_keyframe(int(frame_idx))
            kf.puppets = kf_data.get("puppets", {})
            kf.objects = kf_data.get("objects", {})

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
        create_blank_scene(win)

def create_blank_scene(win: MainWindow, add_default_puppet: bool = True):
    """Clears the scene and optionally adds a default puppet."""
    for name in list(win.scene_model.puppets.keys()): win.object_manager.delete_puppet(name)
    for name in list(win.scene_model.objects.keys()): win.object_manager.delete_object(name)
    win.object_manager.renderers.clear()
    win.object_manager.graphics_items.clear()
    win.scene_model.keyframes.clear()
    win.timeline_widget.clear_keyframes()
    if add_default_puppet:
        win.object_manager.add_puppet("assets/pantins/manululu.svg", "manu")
    win.playback_handler.update_timeline_ui_from_model()
    win.inspector_widget.refresh()
