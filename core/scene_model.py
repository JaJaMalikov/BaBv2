from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

from core.puppet_model import Puppet


@dataclass
class SceneObject:
    """Représentation sérialisable d'un objet de la scène."""
    name: str
    obj_type: str
    file_path: str
    x: float = 0
    y: float = 0
    rotation: float = 0
    scale: float = 1.0
    z: int = 0
    attached_to: Optional[tuple[str, str]] = None

    def attach(self, puppet_name: str, member_name: str) -> None:
        self.attached_to = (puppet_name, member_name)

    def detach(self) -> None:
        self.attached_to = None

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise l'objet pour l'export JSON."""
        return {
            "name": self.name,
            "obj_type": self.obj_type,
            "file_path": self.file_path,
            "x": self.x,
            "y": self.y,
            "rotation": self.rotation,
            "scale": self.scale,
            "z": self.z,
            "attached_to": self.attached_to,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SceneObject":
        """Construit un ``SceneObject`` depuis une structure dict."""
        obj = cls(
            name=data.get("name"),
            obj_type=data.get("obj_type"),
            file_path=data.get("file_path"),
            x=data.get("x", 0),
            y=data.get("y", 0),
            rotation=data.get("rotation", 0),
            scale=data.get("scale", 1.0),
            z=data.get("z", 0),
        )
        attached = data.get("attached_to")
        if attached is not None:
            obj.attached_to = tuple(attached)
        return obj


@dataclass
class Keyframe:
    """Snapshot de l'état de la scène à un temps donné."""
    index: int
    objects: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    puppets: Dict[str, Dict[str, Dict[str, Any]]] = field(default_factory=dict)

class SceneModel:
    def __init__(self):
        self.puppets = {}    # name -> Puppet instance
        self.objects = {}    # name -> SceneObject
        self.keyframes = {}  # index -> Keyframe
        self.current_frame = 0
        self.start_frame = 0
        self.end_frame = 100
        self.fps = 24
        self.scene_width = 1920
        self.scene_height = 1080
        self.background_path = None

    # -----------------------------
    # PUPPETS ET OBJETS
    # -----------------------------
    def add_puppet(self, name, puppet: Puppet):
        self.puppets[name] = puppet

    def remove_puppet(self, name):
        self.puppets.pop(name, None)

    def add_object(self, scene_object: SceneObject):
        self.objects[scene_object.name] = scene_object

    def remove_object(self, name):
        self.objects.pop(name, None)

    # -----------------------------
    # ATTACHEMENT
    # -----------------------------
    def attach_object(self, obj_name, puppet_name, member_name):
        obj = self.objects.get(obj_name)
        if obj:
            obj.attach(puppet_name, member_name)

    def detach_object(self, obj_name):
        obj = self.objects.get(obj_name)
        if obj:
            obj.detach()

    # -----------------------------
    # KEYFRAMES ET TIMELINE
    # -----------------------------
    def add_keyframe(self, index, puppet_states=None):
        kf = self.keyframes.get(index)
        if not kf:
            kf = Keyframe(index)
            self.keyframes[index] = kf

        for name, obj in self.objects.items():
            kf.objects[name] = obj.to_dict()

        kf.puppets = puppet_states or {}

        self.keyframes = dict(sorted(self.keyframes.items()))
        return kf

    def remove_keyframe(self, index):
        self.keyframes.pop(index, None)

    def go_to_frame(self, index):
        self.current_frame = index
        # La restauration de l'état se fera dans la MainWindow
        # qui a accès aux objets graphiques.

    # -----------------------------
    # IMPORT/EXPORT
    # -----------------------------
    def to_dict(self):
        return {
            "settings": {
                "start_frame": self.start_frame,
                "end_frame": self.end_frame,
                "fps": self.fps,
                "scene_width": self.scene_width,
                "scene_height": self.scene_height,
                "background_path": self.background_path,
            },
            "puppets": list(self.puppets.keys()),
            "objects": {k: v.to_dict() for k, v in self.objects.items()},
            "keyframes": [
                {
                    "index": kf.index,
                    "objects": kf.objects,
                    "puppets": kf.puppets,
                }
                for kf in self.keyframes.values()
            ],
        }

    def from_dict(self, data):
        settings = data.get("settings", {})
        self.start_frame = settings.get("start_frame", 0)
        self.end_frame = settings.get("end_frame", 100)
        self.fps = settings.get("fps", 24)
        self.scene_width = settings.get("scene_width", 1920)
        self.scene_height = settings.get("scene_height", 1080)
        self.background_path = settings.get("background_path")

        self.objects.clear()
        for name, obj_data in data.get("objects", {}).items():
            obj_data["name"] = name
            self.objects[name] = SceneObject.from_dict(obj_data)

        self.keyframes.clear()
        for kf_data in data.get("keyframes", []):
            index = kf_data.get("index")
            if index is None:
                continue
            new_kf = Keyframe(index)
            new_kf.objects = kf_data.get("objects", {})
            new_kf.puppets = kf_data.get("puppets", {})
            self.keyframes[index] = new_kf

        self.keyframes = dict(sorted(self.keyframes.items()))

    def export_json(self, file_path):
        import json
        with open(file_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    def import_json(self, file_path):
        import json
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            # Peupler le modèle depuis les données chargées
            self.from_dict(data)
            return True
        except (IOError, json.JSONDecodeError) as e:
            logging.error(f"Erreur lors du chargement du fichier : {e}")
            return False
        self.from_dict(data)
