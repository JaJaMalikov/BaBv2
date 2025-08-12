# Revue de code : ui/main_window.py

## Aperçu
Fenêtre principale de l'application : orchestre la scène, les widgets (timeline, inspecteur, bibliothèque) et la logique de lecture.

## Points positifs
- Structure générale respectant le modèle-vue-contrôleur défini dans l'AGENTS.md.
- Utilisation de nombreuses méthodes privées pour structurer l'interface (_build_side_overlays, _setup_scene_visuals, etc.).
- Gestion des paramètres utilisateur via `QSettings`.

## Points à améliorer
- Fichier très long (>800 lignes), rendant la maintenance difficile.
- Mélange de logique UI, gestion de l'état et traitement des animations dans la même classe.
- Certaines méthodes (_apply_puppet_states, _apply_object_states) sont complexes avec beaucoup de logique imbriquée.

## Suggestions
- Scinder la classe en composants plus petits (gestion de l'onion skin, sauvegarde/restauration, etc.).
- Documenter davantage les méthodes critiques et ajouter des tests unitaires ciblés.
- Introduire un système de logging plutôt que des `print` et normaliser la gestion des exceptions.
