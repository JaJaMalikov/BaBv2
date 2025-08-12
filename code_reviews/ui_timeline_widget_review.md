# Revue de code : ui/timeline_widget.py

## Observations Générales
- Widget de timeline complet gérant lecture, keyframes, zoom et navigation.
- Utilise une combinaison de boutons, sliders et événements de souris/clavier.

## Points Positifs
- Structure claire avec constantes définissant l'apparence (couleurs, tailles).
- Signaux pour communiquer avec le reste de l'application (`frameChanged`, `fpsChanged`, etc.).

## Problèmes Identifiés
1. Absence de docstrings sur la classe et les méthodes, malgré la complexité du composant.
2. Certaines lignes combinent plusieurs instructions séparées par des `;`, ce qui nuit à la lisibilité.
3. Calculs de zoom et de scrolling dans `wheelEvent` sans limitation de plage explicite.
4. Pas de tests unitaires pour ce widget complexe.

## Recommandations
- Ajouter des docstrings détaillées pour la classe et les méthodes principales.
- Séparer les instructions multiples sur des lignes distinctes pour respecter PEP8.
- Introduire des tests (par exemple, via `QTest`) pour valider les interactions clés.
- Documenter ou limiter les valeurs de `_px_per_frame` pour éviter des comportements extrêmes.
