# Objectifs et Contraintes du Projet

Ce document définit les buts principaux et les limitations techniques et architecturales du projet Macronotron.

## Objectifs Clés

1.  **Application d'Animation 2D :** Développer une application de bureau fonctionnelle et intuitive pour l'animation 2D de marionnettes (puppets) basées sur des fichiers SVG.
2.  **Manipulation Intuitive :** Permettre aux utilisateurs de charger, positionner, et manipuler les marionnettes et autres objets de la scène de manière simple et directe (glisser-déposer, poignées de rotation).
3.  **Animation par Images Clés :** Fournir une timeline avancée permettant de créer des animations fluides via un système d'images clés (keyframes), avec des contrôles de lecture standards (play, pause, boucle).
4.  **Gestion de Scène Complète :** Le système doit gérer des scènes complexes contenant plusieurs marionnettes, des objets SVG, des images d'arrière-plan et des sources lumineuses.
5.  **Personnalisation et Ergonomie :** Offrir une interface utilisateur professionnelle et personnalisable, incluant des panneaux flottants (Inspecteur, Bibliothèque), une gestion de thèmes (import/exportB), et des raccourcis clavier.
6.  **Persistance :** Permettre la sauvegarde et le chargement de l'intégralité de la scène (objets, keyframes, réglages) dans un format de fichier JSON portable.

## Contraintes Clés

1.  **Architecture MVC :** Le projet doit respecter une architecture Modèle-Vue-Contrôleur stricte :
    *   **`core/`** : Logique métier et modèles de données purs, sans aucune dépendance à Qt/PySide6.
    *   **`controllers/`** : Orchestration des interactions entre le modèle et la vue.
    *   **`ui/`** : Implémentation de l'interface graphique avec PySide6.
2.  **Stack Technologique :**
    *   **Langage :** Python 3.10+.
    *   **Bibliothèque UI :** PySide6. Aucune autre bibliothèque de theming externe (ex: `qt-material`) ne doit être ajoutée.
3.  **Format des Données :**
    *   **Scènes :** Sérialisées en JSON, en respectant la structure définie par `SceneModel`.
    *   **Marionnettes :** Définies par des fichiers SVG, avec une configuration de hiérarchie, pivots et Z-order externalisée dans `core/puppet_config.json`.
4.  **Configuration Utilisateur :** Les paramètres de l'interface (géométrie des fenêtres, thèmes, etc.) doivent être gérés via `QSettings` avec l'organisation "JaJa" et l'application "Macronotron".
5.  **Tests :**
    *   Le framework de test est `pytest`.
    *   Les tests d'interface doivent pouvoir s'exécuter en mode "headless" (`QT_QPA_PLATFORM=offscreen`), sans nécessiter d'affichage graphique.
