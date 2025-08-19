from __future__ import annotations

"""Service centralisant les opérations sur le ``SceneModel``.

Rôle et flux de données:
- Fournit une API cohésive et Qt‑agnostique pour modifier le modèle (keyframes,
  pantins, variantes, dimensions, arrière‑plan).
- S'insère dans le flux: UI → Controller → Service → Model → Signaux → View update.
- Aucune référence aux widgets/`QGraphicsItem` ici; les vues s'abonnent aux
  signaux émis pour réagir aux changements (voir ARCHITECTURE.md / Sequence diagrams).
"""

from typing import Callable, Dict, Any, Optional

from PySide6.QtCore import QObject, Signal

from core.scene_model import SceneModel, Keyframe


class SceneService(QObject):
    """Fournit une API de haut niveau pour modifier la scène."""

    background_changed = Signal(object)
    scene_resized = Signal(int, int)

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

    # ------------------------------------------------------------------
    # Pantins
    def add_puppet(self, name: str, puppet: Any) -> None:
        """Ajoute un pantin au modèle."""
        self.model.add_puppet(name, puppet)

    def remove_puppet(self, name: str) -> None:
        """Retire un pantin du modèle."""
        self.model.remove_puppet(name)

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

    # ------------------------------------------------------------------
    # Scène
    def set_background_path(self, path: Optional[str]) -> None:
        """Définit le chemin d'arrière-plan puis émet un signal."""
        self.model.background_path = path
        self.background_changed.emit(path)

    def set_scene_size(self, width: int, height: int) -> None:
        """Met à jour les dimensions de la scène et notifie les vues."""
        self.model.scene_width = int(width)
        self.model.scene_height = int(height)
        self.scene_resized.emit(int(width), int(height))
