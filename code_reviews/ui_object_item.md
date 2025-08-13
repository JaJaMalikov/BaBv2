# Revue de code: ui/object_item.py

## Analyse
Définit des items graphiques pour les objets de la scène (pixmap ou SVG) avec un mixin `_ObjectItemMixin` qui synchronise les transformations avec le modèle.

## Recommandations
- Séparer les responsabilités du mixin pour éviter l'utilisation de variables d'instance dynamiques (`_mw`, `_obj_name`).
- Ajouter des tests pour vérifier la mise à jour des keyframes lors des transformations.
- Envisager d'utiliser des signaux plutôt que d'accéder directement au `MainWindow`.
- Documenter le comportement des classes dérivées `ObjectPixmapItem` et `ObjectSvgItem`.
