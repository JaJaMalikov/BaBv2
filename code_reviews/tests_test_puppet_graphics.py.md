# Revue de code : tests/test_puppet_graphics.py

## Aperçu
Teste la hiérarchie des membres du pantin et la cohérence des pivots lors des transformations.

## Points forts
- Utilisation de fixtures `pytest` pour gérer l'application Qt.
- Vérifie à la fois la hiérarchie logique et les positions après rotation/déplacement.

## Points à améliorer
- L'import du module `os` manque alors que `os.environ` est utilisé.
- Les tests instancient `MainWindow` plusieurs fois sans nettoyage explicite.

## Recommandations
1. Ajouter `import os` en en-tête du fichier.
2. Utiliser des fixtures `session` pour créer/détruire proprement la `MainWindow`.
3. Ajouter des assertions sur la libération des ressources graphiques si nécessaire.
