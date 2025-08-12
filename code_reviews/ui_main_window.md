# Code Review : ui/main_window.py

## Points positifs
- Classe centrale orchestrant la scène, la timeline, les overlays et la gestion des objets.
- Bonne séparation des responsabilités via des gestionnaires (`ObjectManager`, `PlaybackHandler`).
- Utilisation de `QSettings` pour persister certaines préférences utilisateur.

## Points d'amélioration
- Fichier extrêmement volumineux (>1000 lignes) mêlant création de widgets, logique métier et comportements UI complexes.
- Manque de docstrings et d'annotations de type pour la majorité des méthodes, rendant le code difficile à comprendre.
- Plusieurs blocs `try/except` silencieux; les erreurs sont parfois ignorées.
- Usage de nombreuses valeurs magiques (positions, facteurs d'opacité) sans constantes nommées.

## Recommandations
- Extraire des composants (gestion des overlays, onion skin, commandes de menus) dans des classes ou modules dédiés.
- Documenter les méthodes publiques et ajouter des annotations de type pour faciliter la maintenance.
- Centraliser les constantes (opacités, positions initiales) dans un module de configuration.
- Ajouter des tests d'intégration pour valider la cohérence entre modèle et vue (ex : `update_scene_from_model`).
