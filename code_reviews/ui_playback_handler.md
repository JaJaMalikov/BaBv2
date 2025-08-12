# Code Review : ui/playback_handler.py

## Points positifs
- Séparation claire de la logique de lecture (`play`, `pause`, `next_frame`) du reste de la fenêtre principale.
- Usage intensif des signaux pour communiquer avec d'autres composants.
- Gestion du mode boucle et du réglage de FPS intégrée.

## Points d'amélioration
- Peu de docstrings sur les méthodes publiques, rendant l'intention moins évidente.
- `go_to_frame` effectue une sauvegarde conditionnelle puis met à jour l'état; un découpage en méthodes plus petites faciliterait les tests.
- Absence de contrôle sur des valeurs aberrantes (ex. FPS à 0 dans `set_fps`).

## Recommandations
- Ajouter des docstrings et des annotations de type de retour pour chaque méthode.
- Introduire des vérifications d'arguments (FPS positifs, plages valides) avec gestion d'erreur.
- Couvrir la logique de lecture par des tests unitaires afin de garantir la précision des incréments de frame.
