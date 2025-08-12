# Revue de code : ui/scene_io.py

## Aperçu
Module chargé de sauvegarder et de charger la scène au format JSON ainsi que de réinitialiser l'environnement graphique.

## Points forts
- Sépare la logique d'I/O de la `MainWindow`.
- Gestion du chemin et des paramètres supplémentaires (position/scale des pantins).
- Utilisation de `QTimer` pour synchroniser l'UI après chargement.

## Points à améliorer
- L'import tardif de `logging` rompt la cohérence du style.
- `import_scene` mélange beaucoup de responsabilités (I/O, reconstruction graphique, mise à jour des widgets).
- Peu de validation des données JSON entrantes.

## Recommandations
1. Déplacer `import logging` en tête de fichier et utiliser des messages d'erreur cohérents.
2. Refactoriser `import_scene` en sous-fonctions (chargement, reconstruction, synchronisation UI).
3. Ajouter une validation du schéma JSON pour éviter les plantages sur fichiers corrompus.
