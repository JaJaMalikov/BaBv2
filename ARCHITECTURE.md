# Architecture & Conventions de Signaux/Slots

## Modèle‑Vue‑Contrôleur

Le projet suit une séparation stricte des responsabilités :

- **`core/`** – le *modèle*. On y trouve la logique métier et la sérialisation, sans aucune dépendance à Qt.
- **`controllers/`** – les *contrôleurs*. Ils orchestrent les interactions, appliquent les changements au modèle et relient les signaux des vues.
- **`ui/views/`** – la *vue*. Widgets et panneaux PySide6 qui se contentent d'émettre des signaux décrivant les actions de l'utilisateur.

## Protocols

Pour découpler les modules, certains contrôleurs déclarent des interfaces sous forme de `typing.Protocol` (ex.: `MainWindowProtocol`, `InspectorWidgetProtocol`). Ces protocoles décrivent uniquement les attributs/méthodes nécessaires et facilitent les tests ainsi que la complétion.

## Conventions de signaux/slots

- Déclarer les signaux avec `PySide6.QtCore.Signal`.
- Nommer les signaux en `snake_case` et, lorsque pertinent, utiliser les suffixes `_requested` ou `_changed` (`frame_update_requested`, `current_frame_changed`).
- Les widgets Qt exposant des signaux compatibles avec l'écosystème Qt peuvent conserver une forme camelCase (`frameChanged`).
- Les contrôleurs se connectent aux signaux via `.connect()` et implémentent les slots comme de simples méthodes Python.
- Les vues n'accèdent jamais directement au modèle : toute modification passe par un contrôleur.

## Stratégie de tests

- Tests lancés via `pytest -q` en mode headless (QT_QPA_PLATFORM=offscreen défini dans `tests/conftest.py`).
- Les tests UI privilégient des assertions structurelles (existence de widgets, flags de visibilité, géométries plausibles) plutôt que des vérifications de pixels.
- Éviter les boîtes de dialogue bloquantes : patcher `QDialog.exec` pour ouvrir non bloquant si nécessaire.
- Utiliser `QApplication.processEvents()` ou `QTimer.singleShot(0, ...)` pour laisser l'event loop se stabiliser.
- Pour l'IO de scène, contourner `QFileDialog` et appeler directement `ui.scene.scene_io.export_scene(...)` / `import_scene(...)`.

## Schéma QSettings (JaJa/Macronotron)

Clés principales lues/écrites par l'application :
- geometry/* : `mainwindow`, `library`, `inspector`, `view_toolbar`, `main_toolbar`
- layout/timeline_visible: bool
- ui/* : `icon_dir` (str), `icon_size` (int), `theme` (preset), `theme_file` (str), `font_family` (str)
- ui/custom_params/* : paramètres de thème personnalisés
- ui/style/scene_bg: couleur/asset du fond de scène (optionnel)
- ui/menu/{main,quick,custom}/order: liste/CSV d'actions
- ui/menu/{main,quick,custom}/{action_key}: bool visibilité par action
- ui/menu/custom/visible: bool
- ui/icon_override/{name}: chemin d'icône par clé
- ui/icon_color_{normal,hover,active}: couleurs d'icône
- timeline/* : couleurs diverses et alpha in/out
- shortcuts/* : action -> séquence clavier

Notes :
- Les booléens/entiers peuvent revenir en chaînes ; normaliser via `ui.ui_profile._bool/_int/_float/_color`.
- `SettingsManager.clear()` ne supprime que `geometry/*` et `layout/*` (thème/icônes intacts).

## Contrat IO de scène

- `SceneModel.to_dict()/from_dict()` définissent le format JSON source de vérité (voir `core/scene_model.py`, `core/scene_validation.py`).
- `ui/scene/scene_io.py` ajoute/consomme `puppets_data` : map {root_id -> {path, scale, position, rotation, z_offset}} dérivée de l'état graphique.
- À l'import : la scène est nettoyée, le modèle chargé, les puppets restaurés si les chemins existent, les transformées réappliquées, la timeline/inspecteur rafraîchis, puis une mise à jour visuelle est forcée.
