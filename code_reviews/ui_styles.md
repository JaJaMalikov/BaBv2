# Revue de code: ui/styles.py

## Analyse
Contient la feuille de style globale de l'application et une fonction `apply_stylesheet` pour l'appliquer à l'application Qt.

## Recommandations
- Importer explicitement `logging` utilisé dans `apply_stylesheet` afin d'éviter une NameError.
- Structurer le `STYLE_SHEET` en fichiers externes pour faciliter la maintenance et la personnalisation.
- Éviter la duplication de blocs `DraggableHeader` dans la feuille de style.
- Prévoir un mécanisme de thème clair/sombre en exposant les constantes de couleur.
