# Code Review : tests/test_puppet_graphics.py

## Points positifs
- Vérifie la hiérarchie des pièces du pantin ainsi que la propagation des transformations.
- Utilise le mode offscreen pour exécuter les tests sans interface graphique.

## Points d'amélioration
- Le module `os` n'est pas importé alors qu'il est utilisé pour définir `QT_QPA_PLATFORM`.
- Les instances de `MainWindow` ne sont pas fermées explicitement, ce qui peut laisser des ressources non libérées.
- Les assertions ne couvrent pas la remise à zéro des rotations ou la cohérence des z-order après transformations.

## Recommandations
- Ajouter `import os` en tête de fichier.
- Fermer la fenêtre (`window.close()`) à la fin de chaque test.
- Étendre les tests pour couvrir d'autres membres du pantin et vérifier les z-order.
