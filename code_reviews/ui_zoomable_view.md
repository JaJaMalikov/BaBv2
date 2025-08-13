# Revue de code: ui/zoomable_view.py

## Analyse
Sous-classe de `QGraphicsView` qui ajoute des overlays d'outils (zoom, onion skin, etc.) et gère le drag & drop d'éléments dans la scène.

## Recommandations
- Scinder la construction des overlays en modules ou classes séparées pour améliorer la lisibilité.
- Centraliser les tailles/icônes des boutons pour faciliter le theming.
- Ajouter des vérifications sur le format des données déposées (`LIB_MIME`).
- Couvrir par des tests l'interaction avec les signaux `zoom_requested` et `item_dropped`.
