# Synthèse des actions à mener

## Priorité haute
1. **Corriger les erreurs bloquantes**
   - Ajouter les imports manquants (`re` dans `ui/icons.py`, `os` dans `tests/test_puppet_graphics.py`).
   - Corriger le code inatteignable dans `SceneModel.import_json`.
   - Résoudre les références potentielles non définies (`name` dans `ui/object_item.py`).

2. **Sécuriser les entrées/sorties**
   - Valider les données JSON lors de l'import de scène et ajouter des tests négatifs correspondants.

## Priorité moyenne
3. **Refactorisation structurelle**
   - Scinder `ui/main_window.py` et `ui/object_manager.py` en modules plus petits.
   - Décomposer `ui/timeline_widget.py` et `ui/zoomable_view.py` pour réduire la complexité des méthodes.

4. **Documentation et typage**
   - Ajouter docstrings et annotations de types dans les modules principaux (`core/scene_model.py`, `core/puppet_piece.py`, `ui/inspector_widget.py`, etc.).

## Priorité basse
5. **Optimisations et ergonomie**
   - Introduire une mise en cache dans `ui/library_widget.reload`.
   - Factoriser la création de boutons dans `ui/zoomable_view` et `ui/styles` (suppression de duplications).
6. **Tests additionnels**
   - Étendre les tests pour couvrir les cas d'erreur d'I/O et de données corrompues.
