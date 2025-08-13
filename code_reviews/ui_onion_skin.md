# Revue de code: ui/onion_skin.py

## Analyse
Gère l'affichage des silhouettes précédentes/suivantes (onion skin) pour faciliter l'animation. Clone les items graphiques des keyframes et ajuste opacité et position.

## Recommandations
- Scinder `_add_onion_for_frame` en sous-fonctions pour clarifier la création des clones et leur propagation.
- Mutualiser la logique de recherche de keyframe utilisée ici et dans `StateApplier`.
- Documenter les paramètres d'opacité et de décalage z pour faciliter leur ajustement depuis l'interface.
- Prévoir un nettoyage plus robuste des items en cas d'erreur pour éviter les fuites d'objets Qt.
