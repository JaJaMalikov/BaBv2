# Revue de code : tests/test_puppet_graphics.py

## Aperçu
Tests d'intégration sur la hiérarchie des pièces de pantin et leur comportement lors des translations/rotations.

## Points positifs
- Vérifie la cohérence hiérarchique et la propagation des transformations.
- Utilise `pytest` et des fixtures pour initialiser l'application.

## Points à améliorer
- Le module n'importe pas `os` bien qu'il utilise `os.environ`.
- Modification de `sys.path` à l'exécution, fragile pour la maintenance.
- Pas de nettoyage de la fenêtre `MainWindow` créée pendant les tests.

## Suggestions
- Ajouter `import os` au début du fichier.
- Utiliser des paquets installables ou `pytest` plugins pour gérer le chemin plutôt que `sys.path`.
- Fermer explicitement la fenêtre après le test (`window.close()`).
