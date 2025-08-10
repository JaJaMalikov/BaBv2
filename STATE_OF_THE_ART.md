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
*   `qt-material`: Pour l'application de thèmes visuels.

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
        *   **Barre d'outils principale** pour les actions globales (gestion des panneaux, zoom).
        *   Panoramique dans la vue avec le clic molette.
    *   **Panneaux modulables (Docks)**: La Timeline et l'Inspecteur peuvent être affichés, masqués ou déplacés indépendamment (`F3`, `F4`).
    *   **Poignées de rotation basculables** pour désencombrer la vue.
    *   **Personnalisation de la scène**:
        *   Définition de la taille (largeur/hauteur) de la scène.
        *   Chargement d'une **image d'arrière-plan** qui s'adapte à la scène.

*   **Sauvegarde et Chargement**:
    *   L'ensemble de la scène (marionnettes, objets, keyframes, réglages) est sérialisé dans un fichier `.json`.
    *   Le chargement d'un fichier restaure l'intégralité de l'état de la scène.
    *   Sérialisation des objets via `SceneObject.to_dict` / `SceneObject.from_dict` (incluant rotation/échelle/z et attachements) pour un export fiable.

## État actuel et prochaines étapes possibles

L'application a évolué d'un simple outil d'animation de marionnette à un **logiciel de composition de scène 2D fonctionnel et robuste**. L'interface a été professionnalisée et la gestion de plusieurs objets est désormais possible.

Prochaines étapes :

*   **Exportation d'animation**: Permettre d'exporter l'animation sous forme de séquence d'images ou de vidéo (GIF, MP4).
*   **Système d'Undo/Redo**: Implémenter un historique des actions.
*   **Attachement d'objets**: Finaliser la fonctionnalité permettant d'attacher un objet à un membre de marionnette.
*   **Modes d'interpolation**: Ajouter des courbes d'animation (ease-in, ease-out).
*   **Timeline Multi-pistes**: Afficher et gérer des pistes de keyframes séparées pour chaque objet ou membre dans la timeline.
