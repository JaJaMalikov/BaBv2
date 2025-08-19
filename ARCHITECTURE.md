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


---

## Sequence diagrams (textual) for key flows

### Add keyframe flow
- UI (TimelineWidget) emits: add_keyframe_requested(frame_index)
- Controller (SceneController) receives signal and calls: SceneService.add_keyframe(frame_index)
- Service updates SceneModel.add_keyframe(frame_index) and validates invariants (core/scene_validation.py)
- Service notifies Controller of model change -> Controller triggers UI refresh via adapters

### Onion skin update flow
- UI (TimelineWidget) changes current frame -> signal current_frame_changed(frame_index)
- Playback/SceneController computes neighbor frames to show as onion skins
- UI adapter (scene_view adapter) requests onion clones; caching layer reused if topology unchanged
- Scene visuals update opacity/span according to settings (SettingsManager / future SettingsService)

### Attach object flow
- UI (Inspector) emits attach_requested(child_object, parent_object)
- ObjectController validates that attachment is allowed (no cycles, consistent frames)
- SceneService applies attachment in SceneModel and records state for involved frames
- Controller triggers view adapter to reparent corresponding QGraphicsItems and refresh handles
