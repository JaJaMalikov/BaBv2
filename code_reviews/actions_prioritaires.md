# Actions prioritaires

1. **Corriger les erreurs bloquantes**
   - Ajouter les imports manquants (`QWidget` dans `ui/draggable_widget.py`, `os` dans `tests/test_puppet_graphics.py`).
   - Nettoyer la méthode `import_json` de `core/scene_model.py` (appel redondant à `self.from_dict`).

2. **Améliorer la structure des modules volumineux**
   - Refactoriser `ui/main_window.py`, `ui/object_manager.py` et `ui/inspector_widget.py` en sous-modules plus ciblés.
   - Isoler la logique d'animation et d'onion skin dans des classes dédiées.

3. **Renforcer la robustesse et le logging**
   - Remplacer les `print` par `logging` dans tout le projet.
   - Ajouter des validations et une gestion d'erreurs lors du chargement des fichiers SVG, JSON et des assets.

4. **Documenter et typer le code**
   - Ajouter des docstrings et des annotations de type manquantes (mélange `Dict[str, Any]`, variables ambiguës).
   - Envisager l'utilisation de `dataclasses` pour `SceneObject`, `Keyframe`, `PuppetMember`.

5. **Améliorer les tests et la configuration**
   - Séparer les tests d'intégration lourds en cas unitaires plus ciblés et éviter les modifications de `sys.path`.
   - Épingler les versions dans `requirements.txt` et prévoir un fichier de dépendances de développement.
