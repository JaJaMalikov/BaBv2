# Revue de code: ui/draggable_widget.py

## Analyse
Propose des widgets overlay déplaçables et redimensionnables (`DraggableOverlay`, `PanelOverlay`, `DraggableHeader`) pour les panneaux flottants de l'interface.

## Recommandations
- Mutualiser la logique de drag entre `DraggableOverlay` et `DraggableHeader` pour éviter la duplication.
- Paramétrer les dimensions minimales dans une constante plutôt que codées en dur.
- Gérer les erreurs possibles lors de l'application de l'effet d'ombre en différenciant selon la plateforme.
- Ajouter des tests pour la logique de redimensionnement (calcul des bords).
