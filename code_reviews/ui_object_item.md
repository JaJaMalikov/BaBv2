# Code Review : ui/object_item.py

## Points positifs
- Utilisation d'un mixin (`_ObjectItemMixin`) pour partager la logique entre les items pixmap et SVG.
- Synchronisation automatique de la position/rotation avec le modèle lors de `itemChange`.
- Intégration avec l'inspecteur lorsqu'un item est sélectionné.

## Points d'amélioration
- Aucun docstring pour expliquer le rôle du mixin et les méthodes override.
- Pas de gestion d'erreur fine dans `itemChange`; une exception peut interrompre l'interaction utilisateur.
- Les classes publiques (`ObjectPixmapItem`, `ObjectSvgItem`) pourraient être typées (retours, paramètres).

## Recommandations
- Ajouter des docstrings décrivant l'objectif du mixin et des classes dérivées.
- Limiter la portée du `try/except` dans `itemChange` et enregistrer les erreurs via `logging`.
- Ajouter des annotations de type pour clarifier l'API des constructeurs.
