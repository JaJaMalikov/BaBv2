from __future__ import annotations

"""Controller pour les opérations sur le ``SceneModel`` liées aux objets.

Ce module encapsule la logique métier (ajout, suppression, attachements) et
s'appuie sur un ``ObjectViewAdapter`` pour toutes les interactions Qt.
"""

from typing import Dict, Any, Optional
import logging
from core.naming import unique_name

from core.scene_model import SceneModel, SceneObject, Keyframe
from core.types import SceneSnapshot
from ui.protocols import ObjectViewAdapterProtocol


DUPLICATE_OFFSET = 10


class ObjectController:
    """Manipule les objets du modèle de scène.

    docs/tasks.md §14: centralize transformations, duplication and deletion.
    This controller exposes transformation setters to be used by UI/presenters
    instead of directly mutating models or QGraphicsItems.

    Examples (Qt adapter omitted for brevity):
        >>> oc.add_object(SceneObject('lamp', 'svg', 'assets/objets/marteau.svg'))  # doctest: +SKIP
        >>> oc.set_object_scale('lamp', 1.25)  # doctest: +SKIP
        >>> oc.duplicate_object('lamp')  # doctest: +SKIP
        >>> oc.remove_object('lamp')  # doctest: +SKIP
    """

    _log = logging.getLogger(__name__)

    def __init__(self, model: SceneModel, view_adapter: ObjectViewAdapterProtocol) -> None:
        self.model = model
        self.view = view_adapter
        # Domain event hook (pure Python) to notify UI/adapters about model mutations
        self.on_model_changed: Optional[callable] = None

    # ------------------------------------------------------------------
    # Capture d'état
    def capture_scene_state(self) -> SceneSnapshot:
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
        if self.on_model_changed:
            try:
                self.on_model_changed()
            except Exception:
                self._log.exception("on_model_changed callback failed after add_object")

    def remove_object(self, name: str) -> bool:
        """Supprime un objet du modèle et de la vue.

        Returns:
            bool: True si l'objet existait et a été supprimé, False sinon.
        """
        existed = name in self.model.objects
        # Supprimer toujours côté vue pour nettoyer tout résidu visuel
        self.view.remove_object_graphics(name)
        # Supprimer du modèle si présent
        if existed:
            self.model.remove_object(name)
        if self.on_model_changed and existed:
            try:
                self.on_model_changed()
            except Exception:
                self._log.exception("on_model_changed callback failed after remove_object")
        return existed

    def duplicate_object(self, name: str) -> bool:
        """Duplique un objet existant avec un nom unique et copie profonde de l'état.

        - Conserve le type, le chemin, la rotation, l'échelle et le z-order.
        - Décale la position de DUPLICATE_OFFSET pour éviter le recouvrement.
        - Si l'objet est attaché à un membre de pantin, attache la copie au même parent.

        Returns:
            bool: True si la duplication a réussi, False si l'objet source est introuvable.
        """
        src = self.model.objects.get(name)
        if not src:
            return False
        new_name = unique_name(name, self.model.objects.keys())
        dup = SceneObject(
            new_name,
            src.obj_type,
            src.file_path,
            x=src.x + float(DUPLICATE_OFFSET),
            y=src.y + float(DUPLICATE_OFFSET),
            rotation=src.rotation,
            scale=src.scale,
            z=getattr(src, "z", 0),
        )
        self.add_object(dup)
        # Si l'objet source était attaché, attacher la copie au même parent et persister l'état
        if src.attached_to is not None:
            puppet_name, member_name = src.attached_to
            self.attach_object_to_member(new_name, puppet_name, member_name)
        else:
            self._ensure_keyframe(new_name)
        if self.on_model_changed:
            try:
                self.on_model_changed()
            except Exception:
                self._log.exception("on_model_changed callback failed after duplicate_object")
        return True

    def attach_object_to_member(self, obj_name: str, puppet_name: str, member_name: str) -> bool:
        """Attache un objet à un membre de pantin et enregistre son état.

        Returns:
            bool: True si l'objet a été trouvé et attaché, False sinon.
        """
        state = self.view.attach_object_to_member(obj_name, puppet_name, member_name)
        obj = self.model.objects.get(obj_name)
        if obj:
            obj.attach(puppet_name, member_name)
            self._update_from_state(obj, state)
            self._ensure_keyframe(obj_name)
            if self.on_model_changed:
                try:
                    self.on_model_changed()
                except Exception:
                    self._log.exception("on_model_changed callback failed after attach_object_to_member")
            return True
        return False

    def detach_object(self, obj_name: str) -> bool:
        """Détache un objet de son parent éventuel.

        Returns:
            bool: True si l'objet existait et a été détaché, False sinon.
        """
        state = self.view.detach_object(obj_name)
        obj = self.model.objects.get(obj_name)
        if obj:
            obj.detach()
            self._update_from_state(obj, state)
            self._ensure_keyframe(obj_name)
            if self.on_model_changed:
                try:
                    self.on_model_changed()
                except Exception:
                    self._log.exception("on_model_changed callback failed after detach_object")
            return True
        return False

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
        if self.on_model_changed:
            try:
                self.on_model_changed()
            except Exception:
                self._log.exception("on_model_changed callback failed after create_object_from_file")
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
        if self.on_model_changed:
            try:
                self.on_model_changed()
            except Exception:
                self._log.exception("on_model_changed callback failed after create_light_object")
        return obj.name

    def delete_object_from_current_frame(self, name: str) -> bool:
        """Retire un objet des keyframes à partir de la frame courante.

        Returns:
            bool: True si au moins un état d'objet a été supprimé, False sinon.
        """
        cur: int = self.model.current_frame
        if cur not in self.model.keyframes:
            self.model.add_keyframe(cur, self.capture_scene_state())
        removed_any = False
        for fr, kf in list(self.model.keyframes.items()):
            if fr >= cur and name in kf.objects:
                del kf.objects[name]
                removed_any = True
        self.view.hide_object(name)
        if self.on_model_changed and removed_any:
            try:
                self.on_model_changed()
            except Exception:
                self._log.exception("on_model_changed callback failed after delete_object_from_current_frame")
        return removed_any

    # ------------------------------------------------------------------
    # Transformations centralisées
    def set_light_properties(self, name: str, color_argb: str, cone_angle: float, cone_reach: float) -> bool:
        """Set light-specific properties on a light object and persist state.

        - Updates model fields (color, cone_angle, cone_reach)
        - Updates view via adapter
        - Ensures a keyframe exists and records the effective state

        Returns:
            bool: True si succès, False si l'objet n'existe pas/n'est pas une lumière ou valeurs invalides.
        """
        obj = self.model.objects.get(name)
        if not obj or obj.obj_type != "light":
            return False
        # Update model
        obj.color = str(color_argb)
        try:
            obj.cone_angle = float(cone_angle)
            obj.cone_reach = float(cone_reach)
        except (TypeError, ValueError):
            # Do not proceed on invalid numbers
            return False
        # Update visuals
        state = self.view.set_light_properties(name, obj.color, obj.cone_angle, obj.cone_reach)
        # Persist into keyframe
        self._ensure_keyframe(name)
        kf = self.model.keyframes.get(self.model.current_frame)
        if kf is not None and state:
            kf.objects[name] = state
        if self.on_model_changed:
            try:
                self.on_model_changed()
            except Exception:
                self._log.exception("on_model_changed callback failed after set_light_properties")
        return True

    def set_object_scale(self, name: str, scale: float) -> bool:
        """Set the object scale and persist the state.

        - Validates scale > 0
        - Updates model and view
        - Ensures a keyframe exists and writes the current state

        Returns:
            bool: True si succès, False si l'objet est introuvable ou si l'échelle est invalide.
        """
        if scale <= 0:
            return False
        obj = self.model.objects.get(name)
        if not obj:
            return False
        obj.scale = float(scale)
        state = self.view.set_object_scale(name, float(scale))
        self._ensure_keyframe(name)
        # Overwrite with effective graphics state for fidelity
        kf = self.model.keyframes.get(self.model.current_frame)
        if kf is not None and state:
            kf.objects[name] = state
        if self.on_model_changed:
            try:
                self.on_model_changed()
            except Exception:
                self._log.exception("on_model_changed callback failed after set_object_scale")
        return True

    def set_object_rotation(self, name: str, angle: float) -> bool:
        """Set the object rotation (degrees) and persist state.

        Returns:
            bool: True si succès, False si l'objet est introuvable.
        """
        obj = self.model.objects.get(name)
        if not obj:
            return False
        obj.rotation = float(angle)
        state = self.view.set_object_rotation(name, float(angle))
        self._ensure_keyframe(name)
        kf = self.model.keyframes.get(self.model.current_frame)
        if kf is not None and state:
            kf.objects[name] = state
        if self.on_model_changed:
            try:
                self.on_model_changed()
            except Exception:
                self._log.exception("on_model_changed callback failed after set_object_rotation")
        return True

    def set_object_z(self, name: str, z: int) -> bool:
        """Set the object Z-order and persist state.

        Returns:
            bool: True si succès, False si l'objet est introuvable ou si `z` est invalide.
        """
        obj = self.model.objects.get(name)
        if not obj:
            return False
        try:
            z_int = int(z)
        except (TypeError, ValueError):
            return False
        obj.z = z_int
        state = self.view.set_object_z(name, z_int)
        self._ensure_keyframe(name)
        kf = self.model.keyframes.get(self.model.current_frame)
        if kf is not None and state:
            kf.objects[name] = state
        if self.on_model_changed:
            try:
                self.on_model_changed()
            except Exception:
                self._log.exception("on_model_changed callback failed after set_object_z")
        return True

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
