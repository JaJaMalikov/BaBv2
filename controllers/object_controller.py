from __future__ import annotations

"""Controller pour les opérations sur le ``SceneModel`` liées aux objets.

Ce module encapsule la logique métier (ajout, suppression, attachements) et
s'appuie sur un ``ObjectViewAdapter`` pour toutes les interactions Qt.
"""

from typing import Dict, Any, Optional

from core.scene_model import SceneObject, Keyframe
from ui.contracts import SceneModelContract
from ui.contracts import ObjectViewAdapterContract


class ObjectController:
    """Manipule les objets du modèle de scène."""

    def __init__(
        self, model: SceneModelContract, view_adapter: ObjectViewAdapterContract
    ) -> None:
        self.model = model
        self.view = view_adapter

    # ------------------------------------------------------------------
    # Capture d'état
    def capture_scene_state(self) -> Dict[str, Dict[str, Any]]:
        """Capture l'état courant des pantins et objets visibles."""
        return {
            "puppets": self.view.capture_puppet_states(),
            "objects": self.view.capture_visible_object_states(),
        }

    def snapshot_current_frame(self) -> None:
        """Capture l'état et crée un keyframe à la frame courante."""
        cur: int = self.model.current_frame
        state = self.capture_scene_state()
        self.model.add_keyframe(cur, state)

    # ------------------------------------------------------------------
    # Gestion des objets
    def add_object(self, obj: SceneObject) -> None:
        """Ajoute un objet au modèle et crée son équivalent graphique."""
        self.model.add_object(obj)
        self.view.add_object_graphics(obj)

    def remove_object(self, name: str) -> None:
        """Supprime un objet du modèle et de la vue."""
        self.view.remove_object_graphics(name)
        self.model.remove_object(name)

    def duplicate_object(self, name: str) -> None:
        """Duplique un objet existant avec un nom unique."""
        src = self.model.objects.get(name)
        if not src:
            return
        base = name
        i = 1
        new_name = f"{base}_{i}"
        while new_name in self.model.objects:
            i += 1
            new_name = f"{base}_{i}"
        dup = SceneObject(
            new_name,
            src.obj_type,
            src.file_path,
            x=src.x + 10,
            y=src.y + 10,
            rotation=src.rotation,
            scale=src.scale,
            z=getattr(src, "z", 0),
        )
        self.add_object(dup)
        self._ensure_keyframe(new_name)

    def attach_object_to_member(
        self, obj_name: str, puppet_name: str, member_name: str
    ) -> None:
        """Attache un objet à un membre de pantin et enregistre son état."""
        state = self.view.attach_object_to_member(obj_name, puppet_name, member_name)
        obj = self.model.objects.get(obj_name)
        if obj:
            obj.attach(puppet_name, member_name)
            self._update_from_state(obj, state)
        self._ensure_keyframe(obj_name)

    def detach_object(self, obj_name: str) -> None:
        """Détache un objet de son parent éventuel."""
        state = self.view.detach_object(obj_name)
        obj = self.model.objects.get(obj_name)
        if obj:
            obj.detach()
            self._update_from_state(obj, state)
        self._ensure_keyframe(obj_name)

    def create_object_from_file(
        self, file_path: str, scene_pos: Any | None = None
    ) -> Optional[str]:
        """Crée un objet à partir d'un fichier et l'ajoute à la scène."""
        res = self.view.create_object_from_file(file_path, scene_pos)
        if res is None:
            return None
        obj, state = res
        self.model.add_object(obj)
        cur = self.model.current_frame
        if cur not in self.model.keyframes:
            self.model.add_keyframe(cur, self.capture_scene_state())
        kf: Optional[Keyframe] = self.model.keyframes.get(cur)
        if kf is not None:
            kf.objects[obj.name] = state
        return obj.name

    def create_light_object(self, scene_pos: Any | None = None) -> Optional[str]:
        """Crée un objet lumineux."""
        res = self.view.create_light_object(scene_pos)
        if res is None:
            return None
        obj, state = res
        self.model.add_object(obj)
        cur = self.model.current_frame
        if cur not in self.model.keyframes:
            self.model.add_keyframe(cur, self.capture_scene_state())
        kf = self.model.keyframes.get(cur)
        if kf is not None:
            kf.objects[obj.name] = state
        return obj.name

    def delete_object_from_current_frame(self, name: str) -> None:
        """Retire un objet des keyframes à partir de la frame courante."""
        cur: int = self.model.current_frame
        if cur not in self.model.keyframes:
            self.model.add_keyframe(cur, self.capture_scene_state())
        for fr, kf in list(self.model.keyframes.items()):
            if fr >= cur and name in kf.objects:
                del kf.objects[name]
        self.view.hide_object(name)

    # ------------------------------------------------------------------
    def update_object_state_if_keyframe_exists(
        self, name: str, state: Dict[str, Any]
    ) -> None:
        """Met à jour l'état d'un objet si un keyframe existe à la frame courante.

        Déplace la mutation du modèle hors de la vue (QGraphicsItem) vers le contrôleur,
        tout en conservant le comportement précédent (ne pas créer de keyframe implicite).
        """
        cur: int = self.model.current_frame
        if cur not in self.model.keyframes:
            return
        obj = self.model.objects.get(name)
        if obj is None:
            return
        self._update_from_state(obj, state)
        kf = self.model.keyframes.get(cur)
        if kf is not None:
            kf.objects[name] = obj.to_dict()

    # ------------------------------------------------------------------
    def _update_from_state(self, obj: SceneObject, state: Dict[str, Any]) -> None:
        try:
            obj.x = float(state.get("x", obj.x))
            obj.y = float(state.get("y", obj.y))
            obj.rotation = float(state.get("rotation", obj.rotation))
            obj.scale = float(state.get("scale", obj.scale))
            obj.z = int(state.get("z", obj.z))
        except (TypeError, ValueError):
            pass

    def _ensure_keyframe(self, obj_name: str) -> None:
        cur = self.model.current_frame
        if cur not in self.model.keyframes:
            self.model.add_keyframe(cur, self.capture_scene_state())
        kf: Optional[Keyframe] = self.model.keyframes.get(cur)
        obj = self.model.objects.get(obj_name)
        if kf is not None and obj is not None:
            kf.objects[obj_name] = obj.to_dict()
