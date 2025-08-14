# Agent Instructions: Macronotron Project

#### **1. Mission & Objectif**

Vous êtes un agent IA développeur assigné au projet "Macronotron", un outil d'animation de marionnettes 2D construit avec Python et PySide6. Votre mission est de maintenir et d'étendre les fonctionnalités de l'application en suivant les conventions et les workflows établis.

#### **2. Principes Directeurs**

*   **Respect de l'Architecture :** Le projet suit une architecture de type Modèle-Vue.
    *   La logique métier et les données sont dans `core/`.
    *   Les composants d'interface et la logique de présentation sont dans `ui/`.
    *   La `MainWindow` agit comme le contrôleur principal qui lie les deux. Toute nouvelle fonctionnalité doit respecter cette séparation.
*   **Développement Itératif :** Implémentez les fonctionnalités par petites étapes logiques et vérifiables. Ne regroupez pas plusieurs fonctionnalités non liées en une seule modification.
*   **Lire avant d'Écrire :** Avant toute modification d'un fichier, lisez-le systématiquement avec l'outil `read_file` pour vous assurer que vous travaillez sur la version la plus à jour et pour éviter les erreurs de remplacement.
*   **Documentation Continue :** Après l'implémentation d'une ou plusieurs fonctionnalités significatives, mettez à jour le fichier `STATE_OF_THE_ART.md` pour refléter le nouvel état du projet.

#### **3. Fichiers Clés et Leurs Rôles**

*   `macronotron.py`: **Point d'entrée.** Lance l'application.
*   `ui/main_window.py`: **Contrôleur principal.** Contient la logique de l'application, connecte les signaux de l'interface aux méthodes, et orchestre les mises à jour entre le modèle et la vue. C'est ici que la plupart des nouvelles fonctionnalités sont intégrées.
*   `core/scene_model.py`: **Modèle de données principal.** Contient l'état de la scène : la liste des keyframes, les réglages de la timeline (FPS, plage), etc. C'est ce qui est sauvegardé/chargé.
*   `core/puppet_model.py`: **Modèle de données statique.** Définit la structure d'un pantin (hiérarchie des os, pivots). À modifier pour ajouter de nouveaux types de marionnettes.
*   `core/puppet_piece.py`: **Vue d'un membre.** Représentation graphique d'une partie du pantin. Contient la logique de rotation et de visibilité des poignées.
*   `ui/timeline_widget.py`: **Widget de la timeline.** Composant UI autonome qui émet des signaux (play, pause, frame changée, etc.) mais ne contient pas de logique métier.
*   `STATE_OF_THE_ART.md`: **Documentation de l'état actuel.** Doit être maintenue à jour.
*   `VISION.md`: **Vision à long terme.** Contient les idées pour la version nomade du projet.

#### **4. Workflows de Développement Communs**

**A. Ajouter une fonctionnalité à la Timeline :**
1.  Modifier `ui/timeline_widget.py` pour ajouter le composant UI (bouton, spinbox...).
2.  Ajouter le `Signal` correspondant dans `TimelineWidget`.
3.  Dans `main_window.py`, connecter ce nouveau signal à une nouvelle méthode (slot).
4.  Implémenter la logique dans cette nouvelle méthode, qui modifiera généralement le `scene_model`.

**B. Ajouter une fonctionnalité au Menu Principal :**
1.  Identifier l'action de menu dans `ui/ui_menu.py`.
2.  Dans `main_window.py`, dans la méthode `setup_menus` ou directement dans `__init__`, connecter le signal `triggered` de l'action à une nouvelle méthode.
3.  Implémenter la logique dans cette nouvelle méthode.

**C. Modifier la Logique de Sauvegarde/Chargement :**
1.  Ajouter le nouvel attribut dans `SceneModel.__init__`.
2.  Mettre à jour `SceneModel.export_json()` pour écrire ce nouvel attribut.
3.  Mettre à jour `SceneModel.import_json()` pour lire ce nouvel attribut.
4.  Dans `MainWindow`, s'assurer que la UI est mise à jour après le chargement (`import_scene`).

#### **5. Commandes et Vérification**

*   **Installation :** `pip install -r requirements.txt`
*   **Tests :** `pytest`
*   **Lancement :** `python macronotron.py`

#### **6. Préférences Utilisateur Importantes**

*   **NE PAS lancer l'application :** L'utilisateur s'occupe de lancer le serveur de développement (`python macronotron.py`). Ne lancez cette commande que si l'utilisateur vous le demande explicitement.
