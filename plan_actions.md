# Plan de refactorisation

## État des lieux du projet

### Architecture générale
- **Modèle** : géré dans `core/` pour les données persistantes et la logique métier.
- **Vue/UI** : gérée dans `ui/` pour les widgets et l’interaction utilisateur.
- **Contrôleur principal** : `MainWindow` orchestre l’ensemble, mais il concentre aujourd’hui beaucoup de responsabilités UI et métier.

### Principales classes et méthodes

| Module | Classe / Fonction | Rôle principal |
|--------|------------------|----------------|
| `core/scene_model.py` | `SceneModel` – add/remove puppets & objects, gestion des keyframes, import/export |
| `core/puppet_model.py` | `PuppetMember`, `Puppet` – structure hiérarchique d’un pantin et chargement depuis un SVG |
| `core/puppet_piece.py` | `PuppetPiece` – item graphique d’un membre, rotation, gestion des poignées |
| `ui/main_window.py` | `MainWindow` – instancie la scène, la vue (`ZoomableView`), les docks, relie signaux/slots, gère zoom et keyframes |
| `ui/object_manager.py` | `ObjectManager` – création/suppression/manipulation de puppets et objets dans la scène, capture d’état, duplication, attach/detach |
| `ui/timeline_widget.py` | `TimelineWidget` – widget autonome pour la timeline, signaux pour play/pause, ajout/suppression de keyframes, dessin custom |
| `ui/playback_handler.py` | `PlaybackHandler` – contrôle de la lecture, synchronisation timeline/modèle, gestion du timer |
| `ui/zoomable_view.py` | `ZoomableView` – QGraphicsView avec overlay d’outils, drag&drop, zoom souris, signaux pour handles/onion/drops |
| `ui/inspector_widget.py` | `InspectorWidget` – liste des objets/pantins, édition de l’échelle/rotation/z, attach/detach |
| `ui/scene_visuals.py` | `SceneVisuals` – décorations de la scène, gestion du fond et de la bordure |
| `ui/state_applier.py` | `StateApplier` – interpolation et application des poses/états depuis le modèle sur les items graphiques |
| `ui/onion_skin.py` | `OnionSkinManager` – affichage des “fantômes” (frames précédentes/suivantes) |
| `ui/library_widget.py` | `LibraryWidget` – gestion de la bibliothèque d’assets et drag&drop vers la scène |
| `ui/settings_manager.py` | `SettingsManager` – sauvegarde et restauration de la géométrie, docks et overlays |
| `ui/panels.py` | `build_side_overlays`, `position_overlays` – construction/positionnement des overlays Library & Inspector |

### Constats
- **`MainWindow` est très chargée**, mélangeant instanciation, connexions de signaux, logique de scène, gestion d’overlays et de paramètres.
- **Modifications UI dispersées** : `MainWindow`, `ZoomableView`, `SceneVisuals`, `StateApplier`, `ObjectManager` et `OnionSkinManager` possèdent chacun des bouts de code affectant la scène ou l’affichage.
- **Couplage fort** entre `MainWindow` et plusieurs modules (ex. `ObjectManager`, `InspectorWidget`) via accès direct aux attributs, rendant les responsabilités floues.

## Plan de refactorisation

### 1. Clarifier les responsabilités
- **Modèle (`core/`)** : conserver uniquement des structures de données et méthodes de sérialisation.
- **Vue (`ui/`)** : widgets et éléments graphiques. Toute mise à jour visuelle doit être déclenchée via signaux ou méthodes dédiées.
- **Contrôleurs** :
  - Garder `MainWindow` comme orchestrateur léger (gestion de fenêtres, menus, connections de signaux).
  - Déporter la logique spécifique dans des gestionnaires dédiés :
    - [x] `SceneController` pour la synchronisation modèle → scène (`StateApplier`, `SceneVisuals`, `OnionSkinManager`).
    - [x] `UIController` ou `OverlayManager` pour la construction/positionnement des overlays, menus, paramètres.
    - [x] `PlaybackController` (renommer ou étendre `PlaybackHandler`) pour tout ce qui touche timeline et lecture.

### 2. Centraliser la manipulation de la scène
- **Regrouper tout le code de modification graphique** dans un module contrôleur (ex. `SceneController`) :
  - [x] Mise à jour du fond et dimension de scène
  - [x] Onion skin
  - [x] Visibilité des poignées de rotation
  - [ ] Ajout/suppression d’items
  - `MainWindow` ne ferait que déléguer (`scene_controller.add_object(...)` etc.).
- **`ObjectManager`** : limiter à la création/duplication/paramétrage des items (membres, objets).
  Les interactions avec le modèle (`SceneModel`) pourraient passer par un service intermédiaire pour réduire le couplage.

### 3. Réduire la taille de `MainWindow`
- Extraire les blocs de code “utilitaires” en méthodes privées ou modules :
  - [x] Construction des overlays (`build_side_overlays`, `position_overlays`) déjà isolée : étendre la logique pour toute manipulation UI.
  - [x] Paramètres & sauvegarde d’état → `SettingsManager` (déjà existant), `open_settings_dialog`.
- Remplacer les accès directs aux attributs par des signaux/slots, par ex. :
  - [ ] `ZoomableView` émet un signal `zoom_requested` → `SceneController.zoom(factor)`.
  - [ ] `TimelineWidget` émet des signaux → `PlaybackController` gère le modèle.

### 4. Organiser par fonctionnalités
- Créer des **modules ou packages par fonctionnalité** (par ex. `animation`, `library`, `inspector`, `scene`).
  Chaque package contient son widget + son contrôleur, avec une API claire.
- Déplacer toutes les actions `app_actions` vers des sous-modules liés à ces packages, pour que chaque action soit proche de la fonction qu’elle déclenche.

### 5. Améliorer la testabilité et la maintenance
- Introduire des interfaces/abstractions simples pour `SceneModel` (ex. via protocoles ou classes de base), facilitant les tests unitaires.
- [x] Ajouter des **tests ciblés** pour chaque contrôleur/widget extrait. *(début: test `SceneController.set_scene_size`)*
- Documenter chaque module avec un résumé de son rôle et des signaux émis/reçus.

### 6. Nettoyer et documenter
- [x] Compléter `STATE_OF_THE_ART.md` au fur et à mesure des refactors.
- Ajouter des docstrings courtes à chaque méthode non triviale.
- [x] Mettre en place un **guide de style interne** (ex. via `AGENTS.md`) pour uniformiser noms, commentaires et structure.
 
