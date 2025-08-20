from __future__ import annotations

"""Service centralisant les opérations sur le ``SceneModel``.

Rôle et flux de données:
- Fournit une API cohésive et Qt‑agnostique pour modifier le modèle (keyframes,
  pantins, variantes, dimensions, arrière‑plan).
- S'insère dans le flux: UI → Controller → Service → Model → Signaux → View update.
- Aucune référence aux widgets/`QGraphicsItem` ici; les vues s'abonnent aux
  signaux émis pour réagir aux changements (voir ARCHITECTURE.md / Sequence diagrams).
"""

from typing import Callable, Dict, Any, Optional, Tuple

import logging
from PySide6.QtCore import QObject, Signal

from core.scene_model import SceneModel, Keyframe
from core import scene_validation


class SceneService(QObject):
    """Fournit une API de haut niveau pour modifier la scène.

    Examples:
        >>> svc.set_background_path('assets/background/bureaumanu.png')  # doctest: +SKIP
        >>> svc.set_scene_size(1920, 1080)  # doctest: +SKIP
        >>> svc.add_keyframe(12)  # doctest: +SKIP
    """

    _log = logging.getLogger(__name__)

    background_changed = Signal(object)
    scene_resized = Signal(int, int)
    model_changed = Signal()

    def __init__(
        self,
        model: SceneModel,
        state_provider: Callable[[], Dict[str, Dict[str, Any]]],
    ) -> None:
        super().__init__()
        self.model = model
        self._state_provider = state_provider

    # ------------------------------------------------------------------
    # Keyframes
    def add_keyframe(self, frame_index: int) -> None:
        """Capture l'état courant et ajoute un keyframe."""
        state = self._state_provider()
        self.model.add_keyframe(frame_index, state)
        self.model_changed.emit()

    # ------------------------------------------------------------------
    # Pantins
    def add_puppet(self, name: str, puppet: Any) -> None:
        """Ajoute un pantin au modèle."""
        self.model.add_puppet(name, puppet)
        self.model_changed.emit()

    def remove_puppet(self, name: str) -> None:
        """Retire un pantin du modèle."""
        self.model.remove_puppet(name)
        self.model_changed.emit()

    def set_member_variant(self, puppet_name: str, slot: str, variant_name: str) -> None:
        """Enregistre la variante choisie pour un slot de pantin."""
        cur = int(self.model.current_frame)
        if cur not in self.model.keyframes:
            self.add_keyframe(cur)
        kf: Optional[Keyframe] = self.model.keyframes.get(cur)
        if kf is None:
            return
        pup_map = kf.puppets.setdefault(puppet_name, {})
        vmap = pup_map.setdefault("_variants", {})
        vmap[str(slot)] = str(variant_name)
        self.model_changed.emit()

    # ------------------------------------------------------------------
    # Scène (mutations)
    def set_background_path(self, path: Optional[str]) -> None:
        """Définit le chemin d'arrière-plan puis émet un signal.

        Applies basic validation via core.scene_validation before mutation
        (docs/tasks.md §9). Invalid values are ignored and a warning is logged.
        """
        if not scene_validation.validate_settings({"background_path": path}):
            self._log.warning("Rejected invalid background_path", extra={"path": path})
            return
        self.model.background_path = path
        self.background_changed.emit(path)
        self.model_changed.emit()

    def set_scene_size(self, width: int, height: int) -> None:
        """Met à jour les dimensions de la scène et notifie les vues.

        Validates dimensions via core.scene_validation before applying. Negative
        sizes are rejected (docs/tasks.md §9).
        """
        if not scene_validation.validate_settings({"scene_width": width, "scene_height": height}):
            self._log.warning("Rejected invalid scene size", extra={"width": width, "height": height})
            return
        self.model.scene_width = int(width)
        self.model.scene_height = int(height)
        self.scene_resized.emit(int(width), int(height))
        self.model_changed.emit()

    # ------------------------------------------------------------------
    # Scène (requêtes)
    def get_scene_size(self) -> Tuple[int, int]:
        """Retourne (width, height) courants de la scène."""
        return int(self.model.scene_width), int(self.model.scene_height)

    def get_background_path(self) -> Optional[str]:
        """Retourne le chemin d'arrière-plan courant (ou None)."""
        return self.model.background_path

    def get_current_frame(self) -> int:
        """Index de frame courant dans le modèle."""
        return int(self.model.current_frame)

    def get_keyframe(self, index: int) -> Optional[Keyframe]:
        """Retourne le keyframe à l'index donné, s'il existe (sinon None)."""
        return self.model.keyframes.get(int(index))

    def get_model_snapshot(self) -> Dict[str, Dict[str, Any]]:
        """Retourne un instantané minimal lisible par l'UI (objets, puppets).

        Note: on expose une vue en lecture seule du contenu utile, sans renvoyer
        d'objets mutables du modèle lui‑même.
        """
        # Construire une structure triviale à partir de l'état courant
        kf = self.model.keyframes.get(self.get_current_frame())
        objects = kf.objects if kf else {}
        puppets = kf.puppets if kf else {}
        return {"objects": dict(objects), "puppets": dict(puppets)}

    # ------------------------------------------------------------------
    # Validation
    def validate_settings(self, data: Any) -> bool:
        """Valide un bloc de paramètres de scène via core.scene_validation.

        Cette méthode permet à l'UI d'effectuer une validation avant d'appliquer
        des changements, sans importer le module de validation côté UI.
        """
        return scene_validation.validate_settings(data)
