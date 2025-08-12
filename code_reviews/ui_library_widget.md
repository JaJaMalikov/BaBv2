# Code Review : ui/library_widget.py

## Points positifs
- Interface de bibliothèque avec drag-and-drop permettant d'ajouter facilement des ressources.
- Séparation par catégories (arrière-plans, objets, pantins) via un `QTabWidget`.
- Utilisation de `payload` JSON pour transporter les métadonnées lors du glisser-déposer.

## Points d'amélioration
- Très peu de docstrings; certaines méthodes comme `reload` mériteraient une description.
- Gestion d'erreur minimale lors du chargement des icônes ou des fichiers inexistants.
- Les chemins d'accès (`asset_dirs`) sont codés en dur; une configuration externe améliorerait la portabilité.

## Recommandations
- Ajouter des docstrings et annotations de type pour clarifier l'API de `_DraggableGrid` et `LibraryWidget`.
- Enrichir la gestion d'erreurs (fichiers manquants, formats non supportés) avec des logs.
- Paramétrer les répertoires racine via un fichier de configuration ou des arguments.
