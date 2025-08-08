# État des lieux de l'application "Borne and the Bayrou - Disco MIX"

## Objectif de l'application

L'application "Borne and the Bayrou - Disco MIX" est un outil d'animation 2D basé sur des marionnettes (puppets). Il permet de charger des personnages définis dans des fichiers SVG, de les manipuler, de créer des animations fluides via un système d'images clés (keyframes) et de sauvegarder le travail.

## Architecture

L'application est construite en Python avec la bibliothèque d'interface graphique **PySide6**. Elle suit une architecture qui sépare la logique de l'application (le "modèle") de sa représentation graphique (la "vue").

*   **`core/`**: Contient la logique métier.
    *   `puppet_model.py`: Définit la structure hiérarchique de la marionnette.
    *   `svg_loader.py`: Utilitaire pour charger et analyser les fichiers SVG.
    *   `scene_model.py`: Gère l'état de la scène, y compris les marionnettes, les objets, la structure des keyframes et les paramètres de la timeline.
    *   `puppet_piece.py`: Représente un membre de la marionnette dans la scène graphique, gérant sa rotation et ses interactions.

*   **`ui/`**: Contient les composants de l'interface utilisateur.
    *   `main_window.py`: La fenêtre principale qui assemble tous les éléments.
    *   `ui_menu.py`: Fichier généré définissant la structure des menus.
    *   `timeline_widget.py`: Le widget interactif pour la timeline, incluant le curseur, les boutons et l'affichage des keyframes.

*   **`macronotron.py`**: Point d'entrée de l'application.
*   **`assets/`**: Contient les ressources graphiques (SVG).
*   **`tests/`**: Contient les tests unitaires.
*   **`ts_vite/`**: Portage TypeScript du projet utilisant Vite.

## Dépendances

*   `PySide6`: Bibliothèque pour l'interface graphique.
*   `qt-material`: Pour l'application de thèmes visuels.

## Fonctionnalités clés implémentées

*   **Chargement de marionnettes SVG**: L'application décompose un SVG en membres de marionnette basés sur les groupes de calques.
*   **Manipulation hiérarchique**: Les membres sont liés (parent-enfant). Déplacer un parent déplace ses enfants.
*   **Timeline et Keyframing**: Une timeline interactive permet de définir et **supprimer** des keyframes pour sauvegarder la pose du pantin à un instant T.
*   **Interpolation des mouvements**: L'application calcule et affiche de manière fluide les poses intermédiaires entre les keyframes, permettant une animation lisse.
*   **Contrôles de Lecture Avancés**:
    *   Un bouton Play/Pause permet de lire l'animation en temps réel.
    *   La **vitesse de lecture (FPS)** est entièrement réglable.
    *   Une **plage de lecture (Start/End)** peut être définie pour travailler en boucle sur des segments spécifiques de l'animation.
*   **Visualisation et Ergonomie (UI/UX)**:
    *   **Marqueurs de Keyframes**: Des marqueurs visuels clairs sont dessinés sur la timeline.
    *   **Poignées de rotation basculables**: Les poignées pour la manipulation des membres peuvent être affichées ou masquées pour ne pas surcharger la vue.
    *   **Timeline escamotable**: Le panneau de la timeline peut être masqué via le menu pour maximiser l'espace de travail sur la scène.
*   **Sauvegarde et Chargement**: L'ensemble de la scène d'animation, y compris toutes les keyframes et les réglages de la timeline (FPS, plage de lecture), peut être sauvegardé dans un fichier `.json` et rechargé ultérieurement.

## État actuel et prochaines étapes possibles

L'application est devenue un outil d'animation 2D fonctionnel et flexible, avec un workflow complet. Les prochaines étapes pourraient inclure :

*   **Exportation d'animation**: Permettre d'exporter l'animation sous forme de séquence d'images ou de vidéo (GIF, MP4).
*   **Système d'Undo/Redo**: Implémenter un historique des actions pour annuler et rétablir les modifications.
*   **Gestion de plusieurs objets/marionnettes**: Améliorer l'interface pour gérer plusieurs éléments dans une même scène.
*   **Modes d'interpolation**: Ajouter des courbes d'animation (ease-in, ease-out) pour des mouvements plus expressifs.
*   **Amélioration de l'UI/UX**: Continuer à affiner l'interface, ajouter des raccourcis clavier et améliorer le retour visuel pour l'utilisateur.