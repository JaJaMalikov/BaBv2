# État des lieux de l'application "Borne and the Bayrou - Disco MIX"

## Objectif de l'application

L'application "Borne and the Bayrou - Disco MIX" est un outil de composition et d'animation 2D basé sur des marionnettes (puppets). Il permet de charger des personnages (SVG), de les manipuler, de gérer plusieurs objets dans une scène, de créer des animations via un système d'images clés (keyframes) et de sauvegarder le projet.

## Architecture

L'application est construite en Python avec la bibliothèque d'interface graphique **PySide6**. Elle suit une architecture qui sépare la logique de l'application (le "modèle") de sa représentation graphique (la "vue").

*   **`core/`**: Contient la logique métier.
    *   `puppet_model.py`: Définit la structure hiérarchique de la marionnette.
    *   `svg_loader.py`: Utilitaire pour charger et analyser les fichiers SVG.
    *   `scene_model.py`: Gère l'état complet de la scène : marionnettes, objets, keyframes, et paramètres globaux.
    *   `puppet_piece.py`: Représente un membre de la marionnette dans la scène graphique.

*   **`ui/`**: Contient les composants de l'interface utilisateur.
    *   `main_window.py`: La fenêtre principale qui assemble tous les éléments et gère l'essentiel des interactions.
    *   `timeline_widget.py`: Un widget de timeline avancé et interactif.
    *   `inspector_widget.py`: Un panneau pour lister, sélectionner et manipuler les objets de la scène.
    *   `library_widget.py`: Panneau « Bibliothèques » listant les ressources importables.
    *   `ui_menu.py`: Fichier généré définissant la structure des menus.

*   **`macronotron.py`**: Point d'entrée de l'application.
*   **`assets/`**: Contient les ressources graphiques (SVG, images).
*   **`tests/`**: Contient les tests unitaires.

## Dépendances

*   `PySide6`: Bibliothèque pour l'interface graphique.
*   (Retiré) `qt-material`: thème désormais assuré par une feuille de style interne.

## Fonctionnalités clés implémentées

*   **Gestion de Scène Multi-Objets**:
    *   Le modèle de scène peut gérer plusieurs marionnettes et objets (images, SVG) simultanément.
    *   **Inspecteur d'objets**:
        - Liste marionnettes et objets, synchro de sélection scène ↔ inspecteur.
        - Actions: sélectionner, dupliquer, suppression temporelle depuis la frame courante.
        - Contrôles objet: échelle, rotation (autour du centre), z-order.
        - Attachements: lier/détacher un objet à un membre de marionnette (suivi des mouvements).
    *   **Bibliothèques (nouveau)**:
        - Catégories: `assets/background`, `assets/objets`, `assets/pantins`.
        - Import par glisser-déposer vers la scène ou clic droit « Ajouter à la scène ».
        - Vignettes (PNG/JPG/SVG) et infobulles chemin.

*   **Marionnettes et Animation**:
    *   Chargement de marionnettes depuis des fichiers SVG.
    *   Manipulation hiérarchique (les enfants suivent les parents).
    *   Interpolation fluide des mouvements entre les keyframes pour une animation lisse.

*   **Timeline Avancée**:
    *   La timeline a été entièrement réécrite pour une expérience professionnelle.
    *   **Zoom et Panoramique**: Navigation intuitive dans la timeline avec `Ctrl+Molette` pour le zoom et le clic molette pour le panoramique.
    *   **HUD interactif**: Affiche en temps réel le numéro de l'image et le temps sous le curseur.
    *   Gestion des keyframes sur une piste "Globale" et spinboxes In/Out dans la barre d'outils.
    *   Contrôles de lecture complets (Play/Pause, Stop, Boucle).

*   **Interface Utilisateur et Ergonomie (UI/UX) Améliorées**:
    *   **Vue de la scène professionnelle**:
        *   **Barre d'outils flottante (Overlay)** directement sur la vue pour un accès rapide au zoom, centrage, et affichage/masquage des poignées de rotation.
        *   **Barre d'outils principale rétractable** regroupée avec la barre d'outils flottante.
        *   Panoramique dans la vue avec le clic molette.
*   **Panneaux / Overlays**:
    *   Timeline: reste un Dock (ancré en bas, closable).
    *   Inspecteur et Bibliothèque: fonctionnent comme des overlays flottants (drag par bordure ou par un en-tête HUD).
    *   **Poignées de rotation basculables** pour désencombrer la vue.
    *   **Onion skinning (fantômes)**: affichage des poses des frames précédentes/suivantes en surimpression (toggle overlay).
    *   **Personnalisation de la scène**:
        *   Définition de la taille (largeur/hauteur) de la scène.
        *   Chargement d'une **image d'arrière-plan** qui redimensionne automatiquement la scène.
    *   **Styles et constantes unifiés**:
        *   Style des boutons factorisé dans `ui/styles.py` pour cohérence.
        *   Chaîne MIME partagée (`LIB_MIME`) pour le glisser-déposer d'éléments.

*   **Sauvegarde et Chargement**:
    *   L'ensemble de la scène (marionnettes, objets, keyframes, réglages) est sérialisé dans un fichier `.json`.
    *   Le chargement d'un fichier restaure l'intégralité de l'état de la scène.
    *   Sérialisation centralisée via `SceneModel.to_dict` / `from_dict` (incluant objets et keyframes) pour un export fiable.

## Mises à jour récentes

- Correction du chargement JSON: `SceneModel.import_json` peuple désormais correctement le modèle via `from_dict` et retourne un booléen de succès.
- Nettoyage: suppression de code inatteignable dans `SceneModel.import_json` et sécurisation de `ui/object_item.py` pour éviter une référence potentiellement non définie dans les logs.
- Logging renforcé: remplacement des `print` par `logging` dans `ui/scene_io.py` (sauvegarde/chargement) et `core/svg_loader.py` (export de groupe), avec gestion plus précise des exceptions et messages contextualisés. Ajout de logs non intrusifs (niveau debug/warning) dans `ui/main_window.py`, `ui/library_widget.py`, `ui/inspector_widget.py`, `ui/draggable_widget.py`, `ui/object_manager.py` et `ui/icons.py` pour éviter les silences en cas d'erreurs non critiques.
- Refactor Onion Skin: extraction de toute la logique de fantômes (onion skin) dans `ui/onion_skin.py` avec une classe `OnionSkinManager`. `MainWindow` délègue désormais via de simples wrappers (`set_onion_enabled`, `update_onion_skins`, `clear_onion_skins`).
- Refactor UI: extraction de la construction des overlays (Bibliothèque/Inspecteur) dans `ui/panels.py` et de la gestion des visuels de scène (bordure, label des dimensions, image de fond) dans `ui/scene_visuals.py` via la classe `SceneVisuals`. `MainWindow` délègue désormais ces responsabilités et expose des wrappers compatibles.
- Refactor Actions/Signaux: création de `ui/actions.py` pour centraliser la création des `QAction` et le câblage des signaux UI. `MainWindow` utilise `app_actions.build_actions(self)` et `app_actions.connect_signals(self)` pour réduire la taille et améliorer la lisibilité.
- Refactor Settings: création de `ui/settings_manager.py` avec une classe `SettingsManager` qui encapsule la sauvegarde/chargement/clear des réglages (géométries, visibilité de la timeline, positions des overlays). `MainWindow` délègue via des wrappers (`save_settings`, `load_settings`, `reset_ui`).
- Refactor State Applier: extraction de l'application des états keyframes vers les items graphiques dans `ui/state_applier.py` via `StateApplier`. `MainWindow` garde des wrappers (`_apply_puppet_states`, `_apply_object_states`) qui délèguent au nouveau module.
- Interpolation angulaire fiable: l'interpolation des rotations des membres (puppets) suit désormais l'arc le plus court entre deux keyframes (wrap -180..180) afin d'éviter les « grands tours »/sauts lors d'un passage 0°/360°. La position des pièces racines reste interpolée linéairement; les enfants continuent de propager les transforms.
- Interpolation des objets: les objets libres ou attachés interpolent désormais position, rotation (arc le plus court) et échelle entre deux keyframes où l'objet est présent. Le mode d'attache est respecté: interpolation en coordonnées locales si l'objet est attaché au même membre aux deux extrémités; sinon, comportement step (pas d'interpolation) et règles de visibilité inchangées en cas d'apparition/disparition.
- Attache/Détache robustes: lors de l'attache, la rotation/échelle locales de l'objet sont recalculées à partir de son transform monde pour éviter tout décalage; lors du détachement, la rotation, l'échelle et le z-order monde sont “cuites” dans l'objet (baked) afin d'éviter tout saut visuel entre la frame avant/après détachement.
- Snapshot automatique: les opérations d'attache/détache créent une keyframe sur la frame courante si absente, et y enregistrent l'état de l'objet. Cela corrige les objets attachés à la frame 0 qui n'étaient pas persistés (plus de position 0,0 par défaut à la prochaine keyframe).
- Sélection plus sûre: cliquer un membre de pantin nettoie automatiquement la sélection des objets (pour éviter les glissements involontaires d'objets lors des déplacements du pantin). L'inspecteur ne réimpose plus la sélection de l'objet dans la scène lors d'un changement de frame (mise à jour des combos d'attache uniquement).
- Chargement fiable frame 0: après import, la scène applique explicitement l'état de la frame courante même si la frame de départ est identique (évite les objets attachés affichés à 0,0 jusqu'à la prochaine keyframe).
- Indicateur d'attache (UI): dans l'Inspecteur, les objets attachés à la frame courante affichent une petite icône de lien dans la liste pour signaler rapidement leur état.
- Inspecteur contextuel: le panneau d’options (échelle, rotation, z, attache) n’apparaît que lorsqu’un élément est sélectionné dans la liste, évitant d’afficher des valeurs par défaut lorsqu’aucun élément n’est sélectionné.
- Contrôles pantin: l’Inspecteur permet désormais d’ajuster la rotation du pantin entier (autour du pivot de la pièce racine) et un décalage de Z global appliqué à toutes ses pièces (utile pour gérer la profondeur entre plusieurs pantins). Les valeurs par défaut préservent les tests existants (offset Z = 0).
- Sérialisation pantin: les propriétés par-pantin (chemin, échelle, position racine) incluent désormais la rotation globale et l'offset Z (`puppets_data` dans le JSON). À l'import, ces valeurs sont restaurées avant l'application des keyframes.
- Menu Paramètres: ajout d'un QDialog accessible depuis l'overlay d'outils principaux permettant d'ajuster rapidement FPS, plage In/Out, taille de scène, boucle, onion skin, affichage des poignées, et l'image d'arrière-plan (avec navigateur de fichiers). Les changements sont appliqués immédiatement à l'acceptation.
- Paramètres UI avancés: possibilité de définir un dossier d'icônes personnalisé (fallback sur `assets/icons`), et de régler les tailles par défaut des panneaux Bibliothèque/Inspecteur. Ces préférences sont persistées via `QSettings` et utilisées au placement initial des overlays.
- Menu Builder: options pour afficher/masquer les boutons des overlays (Main: sauvegarder, charger, scène, fond, reset scène/UI, toggles bibliothèque/inspecteur/timeline, paramètres; Quick: zoom-/zoom+, fit, poignées, onion). Application immédiate et persistance via `QSettings`.
- Style UI: checkboxes retravaillés (contraste et état coché bien visibles) et légers ajustements des titres de groupes, pour une meilleure lisibilité sur fond clair.
- Refactor Overlays Position: `_position_overlays` déplacée dans `ui/panels.position_overlays(win)` pour centraliser la logique de placement des overlays et barres d’outils.
- Refactor Sélection: synchronisation scène ↔ inspecteur extraite dans `ui/selection_sync.py` (fonctions `select_object_in_inspector` et `scene_selection_changed`). `MainWindow` délègue via des wrappers pour compatibilité.
- Refactor Scene Settings: externalisation de `set_scene_size` dans `ui/scene_settings.py` pour gérer l'entrée utilisateur et l'application (sceneRect, visuels, fond, zoom). `MainWindow` délègue via un wrapper.
- Refactor Scene Commands: externalisation de `reset_scene` et `set_background` dans `ui/scene_commands.py` pour centraliser les commandes de scène interactives. `MainWindow` expose des wrappers qui délèguent.
- Docstrings & Typage: ajout de docstrings et d'annotations de types dans les modules clés:
  - `core/scene_model.py`: annotations complètes pour `SceneObject`, `Keyframe`, `SceneModel` et docstrings de module/classes.
  - `core/puppet_piece.py`: docstrings de classes/méthodes (handles, PuppetPiece) et clarifications.
  - `core/puppet_model.py`: docstrings de module/classes/fonctions (Puppet, PuppetMember, `compute_child_map`).
  - `ui/inspector_widget.py`: docstrings classe/méthodes et types pour callbacks.
  - `ui/library_widget.py`: docstring de module/classe et annotation `reload()`.
  - `ui/timeline_widget.py`: docstring de classe pour préciser le rôle et les signaux exposés.
- Suppression temporelle des objets: la logique d'affichage considère désormais le dernier keyframe ≤ frame courante comme point de vérité. Si ce keyframe ne référence pas un objet, celui-ci est masqué à partir de cette frame (et jusqu'à ce qu'un nouveau keyframe le réintroduise). L’inspecteur se synchronise sur cette règle.
- Nettoyage historique: retrait des vestiges `grid` / `snap_to_grid` dans `PuppetPiece` (non utilisés), sans impact sur le comportement actuel.
- (Revert) Affichage unifié des membres retiré: l'approche basée sur `shape()` des SVG produit des bboxes rectangulaires non conformes. À revisiter ultérieurement avec une extraction de silhouette par rendu offscreen si nécessaire.
- Suppression de la dépendance `qt-material`: le thème est désormais assuré par une feuille de style interne (dark) appliquée dans `MainWindow`.
- Suppression de la StatusBar: le statut de zoom est affiché uniquement dans l'overlay flottant (libérant l'espace et uniformisant l'UI vers un modèle d'overlays transparents).
- Modularisation du StateApplier: `apply_object_states` délègue désormais l'interpolation, l'application directe et le calcul des parents à des fonctions privées testées.
- Système d'icônes local: `ui/icons.py` charge désormais des icônes depuis `assets/icons` (SVG ou PNG) avec fallback vers des pictos vectoriels dessinés à la volée. Pour remplacer une icône, déposer un fichier sous l'un des noms supportés: `save`, `open`, `plus`, `minus`, `fit`, `rotate`, `chevron_left`, `chevron_right`, `scene_size`, `background`, `library`, `inspector`, `timeline`, `onion`.
- Thème "carte rouge": unification visuelle autour d'un accent rouge (boutons overlays translucides rouges, sélections rouges dans listes/arbres, tooltips rouges). Overlays restent flottants et mobiles.
- Inspector: boutons d'action remplacés par des `QToolButton` iconifiés (dupliquer, supprimer, lier/détacher) pour plus de clarté; contrôles regroupés et allégés visuellement.
- Bibliothèque: vignettes plus grandes (64px), lignes alternées, hiérarchie plus lisible.
- Overlays géants (nouveau): Inspecteur et Bibliothèque sont désormais de vrais overlays flottants avec en-tête HUD (titre + fermer), déplaçables au clic gauche sur l'en-tête ou la bordure.
- Overlays menus: ouverts par défaut et positionnés en haut de l'écran, entre Bibliothèque (gauche) et Inspecteur (droite), styles unifiés et sobres (hover/checked neutres).
- Démarrage plus propre: la scène fait un fit automatique, le cadre/dimensions de la scène sont à nouveau visibles, pas de pantin par défaut.
- Bibliothèque UX: double-clic sur un élément pour l'ajouter directement à la scène (en plus du glisser-déposer et menu contextuel).

- Centralisation des poignées de rotation: `SceneController.set_rotation_handles_visible` gère désormais l'affichage des poignées de rotation au lieu de `MainWindow`. Un test unitaire couvre également `SceneController.set_scene_size`.
- **Centralisation de la logique de scène** : Les méthodes de manipulation de la scène (ajout/suppression/duplication d'objets et de marionnettes) ont été déplacées de `ObjectManager` vers `SceneController` pour une meilleure séparation des responsabilités. `ObjectManager` se concentre désormais sur la gestion des données des objets et des marionnettes, tandis que `SceneController` gère leur représentation et leur manipulation dans la scène.

- Capture de scène unifiée : `ObjectManager` expose désormais `capture_scene_state`, permettant à `SceneModel.add_keyframe` de recevoir directement les états des objets et marionnettes sans dupliquer la logique de sérialisation.

- Refactor `SceneObject` et `Keyframe` : conversion en `dataclasses` afin de simplifier l'initialisation et la sérialisation.

- Renforcement du traitement d'erreurs : remplacement des `except Exception` génériques par des exceptions ciblées ou des journaux détaillés.
- Typage renforcé : introduction de `MainWindowProtocol` pour documenter les attributs attendus par `SceneController` et éliminer l'usage de `Any`.
- Calcul des transformations des membres : remplacement des trigonométries manuelles par `QTransform` pour composer rotation et translation des pantins.

## État actuel et prochaines étapes possibles

L'application a évolué d'un simple outil d'animation de marionnette à un **logiciel de composition de scène 2D fonctionnel et robuste**. L'interface a été professionnalisée et la gestion de plusieurs objets est désormais possible.

Prochaines étapes :

*   **Exportation d'animation**: Permettre d'exporter l'animation sous forme de séquence d'images ou de vidéo (GIF, MP4).
*   **Système d'Undo/Redo**: Implémenter un historique des actions.
*   **Attachement d'objets**: Finaliser la fonctionnalité permettant d'attacher un objet à un membre de marionnette.
*   **Modes d'interpolation**: Ajouter des courbes d'animation (ease-in, ease-out).
*   **Interpolation angulaire (prioritaire)**:
    - Implémenter une interpolation des rotations par « plus court chemin » (normaliser le delta dans [-180°, +180°] avant lerp) dans `ui/state_applier.py`.
    - Optionnel: « unwrap » des séries d'angles par membre entre keyframes consécutives pour éviter tout saut 0/360 en lecture continue.
    - Ajouter un test ciblé: 350° -> 10° doit interpoler via -20° et non +340°.
### Responsabilités I/O (clarification)

- `core/scene_model.py`:
  - Sérialise/désérialise l’état logique de la scène (réglages, objets, keyframes) via `to_dict` / `from_dict`.
  - `import_json`/`export_json` lisent/écrivent ce même état logique.
- `ui/scene_io.py`:
  - Orchestration de la reconstitution graphique: recrée les éléments visuels (marionnettes, objets) dans la scène Qt, applique échelles/positions et synchronise la timeline.
  - Enrichit le JSON avec `puppets_data` (chemins, échelles, position des racines) nécessaire à la reconstitution graphique.

*   **Timeline Multi-pistes**: Afficher et gérer des pistes de keyframes séparées pour chaque objet ou membre dans la timeline.
- Correction Onion Skin: prise en compte de l’échelle courante du pantin pour les fantômes. Les clones appliquent désormais le facteur d’échelle (`setScale`) et les offsets parent→enfant sont multipliés par l’échelle pour conserver la cohésion et la taille du ghost en phase avec le pantin.

### Personnalisation UI: Styles et Icônes (nouveau)

- Aperçu de style enrichi et en direct: l’onglet Styles inclut un panneau d’aperçu (PanelOverlay + en‑tête) avec boutons, champs, checkbox et liste. Toute modification de paramètres (couleurs, preset, opacité, rayon, police) met à jour immédiatement l’aperçu sans cliquer sur « Prévisualiser ».
- Pastilles de couleur: affichage de la couleur actuelle à côté de chaque champ; pour « Fond panneaux », la pastille est rendue sur damier avec l’opacité choisie.
- Onglet Icônes: personnalisation par‑icône via sélection d’un fichier (SVG recommandé; PNG/JPG/ICO supportés). Les overrides sont persistés (`ui/icon_override/<clé>`), un reset par icône ou global est proposé, et l’interface (actions + overlays) se rafraîchit immédiatement. Le dossier global `ui/icon_dir` reste supporté pour les noms standards.
