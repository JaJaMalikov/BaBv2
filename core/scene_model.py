"""Scene data model: puppets, objects, keyframes and settings.

This module contains pure data structures and serialization helpers used by the UI.
"""

from typing import Dict, Any, Optional
import logging
import json
from dataclasses import dataclass, field, asdict
from core.types import ObjectStateMap, PuppetStateMap, SceneSnapshot
from core.puppet_model import Puppet
from core.scene_validation import (
    validate_settings,
    validate_objects,
    validate_keyframes,
)

# Scene JSON schema version. Increment when breaking the serialized format.
SCENE_SCHEMA_VERSION = 1


@dataclass
class SceneObject:
    """Représente un objet générique de la scène.

    Un ``SceneObject`` peut être libre (coordonnées en scène) ou attaché à un
    membre de pantin (coordonnées locales au parent). Les coordonnées/valeurs
    restent des types simples pour une sérialisation JSON facile.
    """

    name: str
    obj_type: str  # "image", "svg", "puppet", "light"
    file_path: str
    x: float = 0
    y: float = 0
    rotation: float = 0
    scale: float = 1.0
    z: int = 0
    attached_to: Optional[tuple[str, str]] = None  # (puppet_name, member_name) ou None

    # Attributs pour les lumières
    color: Optional[str] = None  # ex: "#FFFFE0"
    cone_angle: Optional[float] = None  # en degrés
    cone_reach: Optional[float] = None  # en pixels

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
    attachment, etc.). ``puppets`` maps puppet names to a map of member states.
    """

    index: int
    objects: ObjectStateMap = field(default_factory=dict)
    puppets: PuppetStateMap = field(default_factory=dict)


class SceneModel:
    """Central store for puppets, objects and timeline keyframes.

    Invariants enforced/normalized by this model:
    - Keyframe indices are unique and maintained in strictly increasing order.
    - Object dictionary keys match the ``SceneObject.name`` attribute.
    - Object attachments are either ``None`` or a tuple of two strings
      ``(puppet_name, member_name)``.

    JSON serialization includes a top-level "version" key. Import paths will
    attempt migrations via :meth:`_migrate_data` if the saved version differs
    from the current :data:`SCENE_SCHEMA_VERSION`.
    """

    def __init__(self) -> None:
        """Initialize an empty scene with default settings."""
        self.puppets = {}  # name -> Puppet instance
        self.objects = {}  # name -> SceneObject
        self.keyframes = {}  # index -> Keyframe
        self.current_frame = 0
        self.start_frame = 0
        self.end_frame = 100
        self.fps = 24
        self.scene_width = 1920
        self.scene_height = 1080
        self.background_path = None
        # Accumulates non-fatal issues found during the last import operation
        # Each entry is a dict with context keys like {"type": "object|keyframe", "name"/"index": ..., "issue": str}
        self.import_warnings = []

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
    def add_keyframe(self, index: int, state: Optional[SceneSnapshot] = None) -> Keyframe:
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
    def _validate_data(self, data: Any) -> bool:
        """Validate minimally the loaded scene JSON structure without mutating state.

        Rules (lenient):
        - data must be a dict
        - settings (if present) must be a dict with ints for frames/fps and ints for size
        - objects (if present) must be a dict mapping str -> dict
        - keyframes (if present) must be a list of dict with an integer 'index'
        """
        if not isinstance(data, dict):
            logging.error("root: expected dict, got %s", type(data).__name__)
            return False
        if not validate_settings(data.get("settings")):
            return False
        if not validate_objects(data.get("objects")):
            return False
        if not validate_keyframes(data.get("keyframes")):
            return False
        return True

    def _validate_invariants(self, log_only: bool = False) -> bool:
        """Validate and optionally normalize core invariants.

        - Keyframe indices are unique and stored in ascending order.
        - Object dict keys match each object's ``name``.
        - Attachments are None or a tuple[str, str].

        If ``log_only`` is False, performs normalization in-place; otherwise only logs.
        Returns True if invariants are satisfied after potential normalization.
        """
        ok = True
        # Keyframes uniqueness and ordering
        indices = list(self.keyframes.keys())
        if indices != sorted(indices):
            logging.warning("keyframes not sorted; normalizing order")
            ok = False
            if not log_only:
                self.keyframes = dict(sorted(self.keyframes.items()))
        if len(indices) != len(set(indices)):
            logging.error("duplicate keyframe indices detected")
            ok = False
            # duplicates cannot exist as dict keys; this is a safeguard
        # Object keys vs names, and attachment normalization
        new_objects = {}
        for key, obj in list(self.objects.items()):
            # normalize attachment
            att = obj.attached_to
            if att is not None:
                if isinstance(att, (list, tuple)) and len(att) == 2:
                    a0, a1 = att[0], att[1]
                    if not isinstance(a0, str) or not isinstance(a1, str):
                        logging.warning(
                            "attachment contains non-strings for object %s; clearing", key
                        )
                        ok = False
                        if not log_only:
                            obj.attached_to = None
                    else:
                        # ensure tuple type
                        if not isinstance(att, tuple) and not log_only:
                            obj.attached_to = (a0, a1)
                else:
                    logging.warning("invalid attachment shape for object %s; clearing", key)
                    ok = False
                    if not log_only:
                        obj.attached_to = None
            # ensure object key matches name
            if obj.name != key:
                logging.warning(
                    "object key '%s' mismatches name '%s'; normalizing name to key", key, obj.name
                )
                ok = False
                if not log_only:
                    obj.name = key
            new_objects[key] = obj
        if not log_only:
            self.objects = new_objects
        return ok

    def _migrate_data(self, data: Dict[str, Any], from_version: int) -> Dict[str, Any]:
        """Migrate loaded JSON data to the current schema version.

        Currently a no-op for version 1. Future versions may transform field names
        or structures. Unknown higher versions will be used as-is after validation.
        """
        if from_version == 1:
            return data
        # Add future migrations here, e.g., if from_version == 0: ...
        return data

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the whole scene into a JSON-friendly dictionary.

        Includes a top-level schema version to enable future migrations.
        See docs/plan.md Task 4.
        """
        # Log-only invariant check before exporting
        self._validate_invariants(log_only=True)
        return {
            "version": SCENE_SCHEMA_VERSION,
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
            if not isinstance(obj_data, dict):
                logging.warning(
                    "objects[%s]: expected dict, got %s; skipping", name, type(obj_data).__name__
                )
                self.import_warnings.append({"type": "object", "name": name, "issue": "not a dict"})
                continue
            # Basic required fields checks
            obj_type = obj_data.get("obj_type")
            file_path = obj_data.get("file_path")
            if not isinstance(obj_type, str) or not isinstance(file_path, str):
                logging.warning(
                    "object '%s': missing/invalid 'obj_type' or 'file_path'; skipping", name
                )
                self.import_warnings.append(
                    {
                        "type": "object",
                        "name": name,
                        "issue": "missing or invalid obj_type/file_path",
                    }
                )
                continue
            obj_data["name"] = name
            try:
                self.objects[name] = SceneObject.from_dict(obj_data)
            except Exception as e:  # defensive: ensure partial load continues
                logging.warning("object '%s': error during construction: %s; skipping", name, e)
                self.import_warnings.append(
                    {"type": "object", "name": name, "issue": f"exception: {e}"}
                )
                continue

        self.keyframes.clear()
        for kf_data in data.get("keyframes", []):
            if not isinstance(kf_data, dict):
                logging.warning("keyframes: item is not a dict; skipping: %r", kf_data)
                self.import_warnings.append({"type": "keyframe", "issue": "item not a dict"})
                continue
            index = kf_data.get("index")
            if index is None:
                logging.warning("keyframe without 'index' found; skipping")
                self.import_warnings.append({"type": "keyframe", "issue": "missing index"})
                continue
            if index in self.keyframes:
                logging.warning("duplicate keyframe index %s; last one wins", index)
                self.import_warnings.append(
                    {"type": "keyframe", "index": index, "issue": "duplicate index"}
                )
            new_kf = Keyframe(index)
            new_kf.objects = kf_data.get("objects", {})
            new_kf.puppets = kf_data.get("puppets", {})
            self.keyframes[index] = new_kf

        self.keyframes = dict(sorted(self.keyframes.items()))
        # Normalize/enforce invariants for direct from_dict usage as well
        self._validate_invariants(log_only=False)

    def export_json(self, file_path: str) -> None:
        """Export the scene to a JSON file at ``file_path``.

        Progress feedback: logs start/end with counts to help diagnose long runs
        (docs/tasks.md 16.2). Behavior is unchanged.
        """
        data = self.to_dict()
        # Validate JSON structure prior to writing for early detection (docs/tasks.md Task 4.25)
        if not self._validate_data(data):
            logging.error("Export JSON invalid: structure non conforme")
        total_objects = len(self.objects)
        total_kf = len(self.keyframes)
        logging.info(
            "Exporting scene JSON → %s (objects=%d, keyframes=%d)",
            file_path,
            total_objects,
            total_kf,
        )
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logging.info("Export complete ← %s", file_path)

    def import_json(self, file_path: str) -> bool:
        """Load scene data from a JSON file, returning success.

        On success, partially invalid entries are skipped and recorded in
        ``self.import_warnings`` along with log messages for developer context.

        Progress feedback: logs start/end with counts to help diagnose long runs
        (docs/tasks.md 16.2). Behavior is unchanged.
        """
        try:
            logging.info("Importing scene JSON ← %s", file_path)
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # reset non-fatal issues log for this import operation
            self.import_warnings = []

            # Determine version and migrate if needed before validation
            from_version = data.get("version", 1)
            if not isinstance(from_version, int):
                logging.warning("scene version is not an int (%r); assuming v1", from_version)
                from_version = 1
            if from_version > SCENE_SCHEMA_VERSION:
                logging.warning(
                    "Loading scene with newer schema version %s (current %s). Attempting best-effort load.",
                    from_version,
                    SCENE_SCHEMA_VERSION,
                )
            elif from_version < SCENE_SCHEMA_VERSION:
                logging.info(
                    "Migrating scene from version %s to %s", from_version, SCENE_SCHEMA_VERSION
                )
                data = self._migrate_data(data, from_version)

            # Validate before applying to avoid partial state
            if not self._validate_data(data):
                logging.error("Import JSON invalide: structure non conforme")
                return False

            self.from_dict(data)
            # Normalize/enforce invariants post-load
            self._validate_invariants(log_only=False)
            logging.info(
                "Import complete ← %s (objects=%d, keyframes=%d, warnings=%d)",
                file_path,
                len(self.objects),
                len(self.keyframes),
                len(self.import_warnings),
            )
            return True
        except (IOError, json.JSONDecodeError) as e:
            logging.error("Erreur lors du chargement du fichier : %s", e)
            return False
