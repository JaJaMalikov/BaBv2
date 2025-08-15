"""Scene data model: puppets, objects, keyframes and settings.

This module contains pure data structures and serialization helpers used by the UI.
"""

from typing import Dict, Any, Optional
import logging
import json
from dataclasses import dataclass, field, asdict
from core.puppet_model import Puppet


@dataclass
# pylint: disable=R0902
class SceneObject:
    """Représente un objet générique de la scène.

    Un ``SceneObject`` peut être libre (coordonnées en scène) ou attaché à un
    membre de pantin (coordonnées locales au parent). Les coordonnées/valeurs
    restent des types simples pour une sérialisation JSON facile.
    """

    name: str
    obj_type: str  # "image", "svg", "puppet"
    file_path: str
    x: float = 0
    y: float = 0
    rotation: float = 0
    scale: float = 1.0
    z: int = 0
    attached_to: Optional[tuple[str, str]] = None  # (puppet_name, member_name) ou None

    def attach(self, puppet_name: str, member_name: str) -> None:
        """Attach object to a puppet member by names."""
        self.attached_to = (puppet_name, member_name)

    def detach(self) -> None:
        """Detach object from any puppet member."""
        self.attached_to = None

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise l'objet pour l'export JSON."""
        return asdict(self)

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
    """Snapshot of the scene state at a given frame.

    ``objects`` maps object names to their state (position, rotation, scale,
    attachment, etc.). ``puppets`` maps puppet names to un dict d'états de membres.
    """

    index: int
    objects: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    puppets: Dict[str, Dict[str, Dict[str, Any]]] = field(default_factory=dict)

# pylint: disable=R0902
class SceneModel:
    """Central store for puppets, objects and timeline keyframes."""

    def __init__(self) -> None:
        """Initialize an empty scene with default settings."""
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
    def add_puppet(self, name: str, puppet: Puppet) -> None:
        """Register a puppet in the scene by name."""
        self.puppets[name] = puppet

    def remove_puppet(self, name: str) -> None:
        """Remove a puppet from the scene if present."""
        self.puppets.pop(name, None)

    def add_object(self, scene_object: SceneObject) -> None:
        """Add a new scene object to the model."""
        self.objects[scene_object.name] = scene_object

    def remove_object(self, name: str) -> None:
        """Remove a scene object by its name if it exists."""
        self.objects.pop(name, None)

    # -----------------------------
    # ATTACHEMENT
    # -----------------------------
    def attach_object(self, obj_name: str, puppet_name: str, member_name: str) -> None:
        """Attach an object to a puppet member."""
        obj = self.objects.get(obj_name)
        if obj:
            obj.attach(puppet_name, member_name)

    def detach_object(self, obj_name: str) -> None:
        """Detach an object from any puppet member."""
        obj = self.objects.get(obj_name)
        if obj:
            obj.detach()

    # -----------------------------
    # KEYFRAMES ET TIMELINE
    # -----------------------------
    def add_keyframe(
        self, index: int, state: Optional[Dict[str, Dict[str, Dict[str, Any]]]] = None
    ) -> Keyframe:
        """Create or overwrite a keyframe at ``index`` with captured puppet and object states.

        ``state`` is expected to contain two keys:

        - ``"objects"``: mapping object name -> serialized state
        - ``"puppets"``: mapping puppet name -> member states

        When ``state`` is ``None`` the current ``SceneObject`` instances are
        serialized directly. This fallback allows pure ``SceneModel`` tests to
        operate without an ``ObjectManager``.
        """
        kf = self.keyframes.get(index)
        if not kf:
            kf = Keyframe(index)
            self.keyframes[index] = kf

        if state is None:
            object_states = {name: obj.to_dict() for name, obj in self.objects.items()}
            puppet_states = {}
        else:
            object_states = state.get("objects", {})
            puppet_states = state.get("puppets", {})

        kf.objects = object_states
        kf.puppets = puppet_states

        self.keyframes = dict(sorted(self.keyframes.items()))
        return kf

    def remove_keyframe(self, index: int) -> None:
        """Delete the keyframe at ``index`` if present."""
        self.keyframes.pop(index, None)

    def go_to_frame(self, index: int) -> None:
        """Set the current frame pointer without applying any state."""
        self.current_frame = index
        # La restauration de l'état se fera dans la MainWindow
        # qui a accès aux objets graphiques.

    # -----------------------------
    # IMPORT/EXPORT
    # -----------------------------
    # pylint: disable=R0911, R0912
    def _validate_data(self, data: Any) -> bool:
        """Validate minimally the loaded scene JSON structure without mutating state.

        Rules (lenient):
        - data must be a dict
        - settings (if present) must be a dict with ints for frames/fps and ints for size
        - objects (if present) must be a dict mapping str -> dict
        - keyframes (if present) must be a list of dict with an integer 'index'
        """
        if not isinstance(data, dict):
            return False
        settings = data.get("settings", {})
        if settings is not None and not isinstance(settings, dict):
            return False
        if isinstance(settings, dict):
            for k in ("start_frame", "end_frame", "fps", "scene_width", "scene_height"):
                if k in settings and not isinstance(settings[k], int):
                    return False
        objects = data.get("objects", {})
        if objects is not None and not isinstance(objects, dict):
            return False
        if isinstance(objects, dict):
            for k, v in objects.items():
                if not isinstance(k, str) or not isinstance(v, dict):
                    return False
        keyframes = data.get("keyframes", [])
        if keyframes is not None and not isinstance(keyframes, list):
            return False
        if isinstance(keyframes, list):
            for kf in keyframes:
                if not isinstance(kf, dict):
                    return False
                idx = kf.get("index")
                if idx is not None and not isinstance(idx, int):
                    return False
        return True
    def to_dict(self) -> Dict[str, Any]:
        """Serialize the whole scene into a JSON-friendly dictionary."""
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

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load scene data from a dictionary produced by :meth:`to_dict`."""
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

    def export_json(self, file_path: str) -> None:
        """Export the scene to a JSON file at ``file_path``."""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    def import_json(self, file_path: str) -> bool:
        """Load scene data from a JSON file, returning success."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Valider avant d'appliquer pour éviter tout état partiel
            if not self._validate_data(data):
                logging.error("Import JSON invalide: structure non conforme")
                return False
            self.from_dict(data)
            return True
        except (IOError, json.JSONDecodeError) as e:
            logging.error("Erreur lors du chargement du fichier : %s", e)
            return False
