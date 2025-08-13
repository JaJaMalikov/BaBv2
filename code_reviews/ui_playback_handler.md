# Revue de code: ui/playback_handler.py

## Analyse
Gestionnaire de lecture synchronisant la timeline, le modèle de scène et l'inspecteur. Émet des signaux pour les mises à jour de frame et l'ajout de keyframes.

## Recommandations
- Ajouter des tests pour les transitions de lecture (boucle, stop, pause) afin de sécuriser les comportements.
- Documenter les effets de `go_to_frame` sur le modèle et la timeline.
- Prévoir la gestion d'une lecture inversée ou du saut de frame pour futures fonctionnalités.
- Éviter les accès directs aux widgets (`play_btn`) en passant par des méthodes dédiées.
