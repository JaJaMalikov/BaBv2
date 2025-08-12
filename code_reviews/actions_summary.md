# Plan d'actions priorisé

1. **Corriger les imports manquants**
   - `ui/styles.py` : ajouter `from PySide6.QtGui import QFont`.
   - `ui/draggable_widget.py` : importer `QWidget`.
   - `ui/icons.py` : ajouter `import re`.
   - `tests/test_puppet_graphics.py` : ajouter `import os`.

2. **Renforcer la documentation et les types**
   - Ajouter docstrings et annotations de type aux classes et méthodes des modules `core` et `ui` (ex. `object_manager`, `timeline_widget`).
   - Documenter les méthodes de tests pour clarifier l'intention.

3. **Refactoriser les modules volumineux**
   - `ui/main_window.py`, `ui/object_manager.py`, `ui/zoomable_view.py` : scinder en sous-modules ou classes pour réduire la complexité.
   - Isoler la logique de timeline de la vue dans `ui/timeline_widget.py`.

4. **Améliorer la gestion des erreurs et le logging**
   - Remplacer les `print` par `logging` dans `core/svg_loader.py` et `ui/scene_io.py`.
   - Affiner les blocs `try/except` génériques et fournir des messages de log explicites.

5. **Étendre la couverture de tests**
   - Ajouter des tests négatifs pour l'import/export de scènes.
   - Tester le comportement du zoom, des overlays et de l'attachement des objets.
   - Fermer explicitement les fenêtres créées dans les tests pour éviter les fuites de ressources.

6. **Centraliser la configuration**
   - Externaliser les grands dictionnaires (`PARENT_MAP`, `PIVOT_MAP`, `Z_ORDER`) et chemins de ressources dans des fichiers de configuration.
   - Factoriser les constantes d'interface (couleurs, opacités, dimensions) dans un module dédié.
