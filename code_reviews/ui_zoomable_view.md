# Code Review : ui/zoomable_view.py

## Points positifs
- Widget de vue enrichi avec commandes de zoom, fit et gestion de l'onion skin.
- Utilisation judicieuse d'un overlay glissable pour regrouper les boutons de contrôle.
- Gestion complète des événements de souris et de drag-and-drop.

## Points d'amélioration
- Fichier volumineux avec beaucoup de logique dans `__init__` et `_build_overlay`; difficile à maintenir.
- Manque de docstrings sur les méthodes, notamment celles gérant les événements.
- Certaines méthodes mettent à jour des attributs créés dynamiquement (`_panning`, `_main_tools_overlay`) sans déclaration préalable.
- Absence de tests unitaires pour les interactions complexes (zoom, overlay repliable).

## Recommandations
- Scinder la construction de l'overlay et des outils principaux dans des classes ou fonctions séparées.
- Ajouter des annotations de type et documenter les interactions de drag-and-drop.
- Initialiser explicitement les attributs utilisés dans les méthodes pour éviter les erreurs de typage.
- Ajouter des tests automatisés pour vérifier le comportement du zoom et des boutons.
