# Revue de code : ui/playback_handler.py

## Observations Générales
- Classe `PlaybackHandler` responsable de la gestion de la lecture et de la synchronisation entre le modèle, la timeline et l'inspecteur.
- Utilise des signaux Qt pour dé-coupler la logique de lecture du reste de l'UI.

## Points Positifs
- Méthodes claires pour play/pause/stop, changement de frame et mise à jour du range.
- Documentation de la classe via une docstring descriptive.

## Problèmes Identifiés
1. Absence de gestion d'erreurs ou de vérifications de bornes dans certaines méthodes (ex. `set_fps`).
2. `next_frame` mélange logique métier et mise à jour de l'UI (`play_btn.setChecked`).
3. Pas de tests unitaires couvrant ce gestionnaire.

## Recommandations
- Ajouter des validations pour les valeurs d'entrée (`fps`, `frame_index`).
- Extraire la mise à jour de l'UI (`play_btn`) hors de `next_frame` pour respecter la séparation des responsabilités.
- Introduire des tests pour la logique de boucle et de gestion de frames.
