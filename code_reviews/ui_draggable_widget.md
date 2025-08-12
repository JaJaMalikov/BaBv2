# Code Review : ui/draggable_widget.py

## Points positifs
- Fournit des overlays déplaçables et redimensionnables utilisables dans différentes parties de l'UI.
- Gestion soignée des effets d'ombre et du redimensionnement via les coins.
- Classes bien séparées (`DraggableOverlay`, `PanelOverlay`, `DraggableHeader`).

## Points d'amélioration
- Le module n'importe pas `QWidget` alors qu'il est utilisé comme classe de base.
- Absence de docstrings pour les méthodes, ce qui limite la compréhension des comportements.
- Certaines sections utilisent des `event.position()` (Qt6) sans vérification de compatibilité Qt5.

## Recommandations
- Ajouter les imports manquants (`from PySide6.QtWidgets import QWidget`).
- Documenter les interactions utilisateur attendues (clic droit vs gauche, zones de redimensionnement).
- Ajouter des tests unitaires de base pour valider le comportement de glisser-déposer et de redimensionnement.
