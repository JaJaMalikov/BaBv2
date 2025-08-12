# Synthèse des actions prioritaires

1. **Refactorisation structurelle**
   - Découper `ui/main_window.py` (718 lignes) et `ui/object_manager.py` (>400 lignes) en modules plus petits pour améliorer la maintenabilité.
   - Séparer la logique métier de l'UI lorsque c'est possible.

2. **Amélioration de la documentation**
   - Ajouter des docstrings et commentaires aux classes et méthodes majeures (notamment dans `core` et `ui/timeline_widget.py`).

3. **Gestion des erreurs et logging**
   - Remplacer les `print` par le module `logging` et éviter les `except Exception: pass`.
   - Spécifier les exceptions attrapées et fournir des messages de log utiles.

4. **Corrections techniques immédiates**
   - Corriger l'import manquant de `os` dans `tests/test_puppet_graphics.py` et de `QWidget` dans `ui/draggable_widget.py`.
   - Supprimer le code mort dans `core/scene_model.py` (`self.from_dict(data)` après `return`).
   - Épingler les versions dans `requirements.txt` pour garantir la reproductibilité.

5. **Tests et couverture**
   - Introduire des tests unitaires pour les composants clés (`ui/timeline_widget.py`, `core/svg_loader.py`, `ui/zoomable_view.py`, etc.).
   - Nettoyer les ressources (fenêtres, QApplications) dans les tests existants pour éviter les fuites.

6. **Qualité du code**
   - Uniformiser le style PEP8 (éliminer les instructions multiples par ligne, camelCase…).
   - Clarifier ou factoriser les méthodes longues (`_build_overlay`, `create_blank_scene`, etc.).

7. **Amélioration UX**
   - Gérer les exceptions lors du chargement d'icônes ou de fichiers SVG pour informer l'utilisateur.
   - Documenter et éventuellement paramétrer les chemins d'accès aux ressources (`ui/library_widget.py`).
