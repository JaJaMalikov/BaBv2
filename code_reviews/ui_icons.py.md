# Revue de code : ui/icons.py

## Aperçu
Gestion centralisée des icônes avec rendu SVG et coloration selon l'état (normal, hover, actif).

## Points forts
- Mise en cache des icônes pour éviter les rechargements.
- Prise en charge de variations de couleur selon l'état de l'icône.

## Points à améliorer
- Le module utilise `re.sub` sans importer le module `re`.
- Les fonctions de compatibilité (`icon_plus`, `icon_minus`, etc.) répètent le même motif.

## Recommandations
1. Ajouter `import re` en tête de fichier pour éviter une `NameError`.
2. Envisager de générer dynamiquement les wrappers de compatibilité pour limiter la duplication.
3. Documenter les conventions de nommage des fichiers SVG attendus dans `assets/icons`.
