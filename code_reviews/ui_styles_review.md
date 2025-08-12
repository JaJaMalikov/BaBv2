# Revue de code : ui/styles.py

## Observations Générales
- Contient la feuille de style globale de l'application ainsi qu'une fonction `apply_stylesheet`.
- L'accent est mis sur un thème clair avec couleurs pastel.

## Points Positifs
- Centralisation des styles facilitant la maintenance visuelle.
- Gestion de la police via `QFont` avec fallback en cas d'absence de "Poppins".

## Problèmes Identifiés
1. Doublon de règles `DraggableHeader` (définies deux fois) pouvant créer de la confusion.
2. Aucune documentation sur les conventions de nommage ou l'organisation des sections CSS.
3. `print` utilisé dans `apply_stylesheet` au lieu de `logging`.

## Recommandations
- Supprimer ou fusionner les déclarations redondantes pour `DraggableHeader`.
- Ajouter des commentaires ou une documentation décrivant les sections du stylesheet.
- Utiliser `logging.warning` plutôt que `print` pour signaler l'absence de police.
