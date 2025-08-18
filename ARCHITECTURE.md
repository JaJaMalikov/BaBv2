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
