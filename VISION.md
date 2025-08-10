# VISION.md: Le MACRON-O-TRON 3000 - Station de Performance Nomade

#### **1. Le Concept : L'Instrument Numérique**

Le **MACRON-O-TRON 3000** est l'évolution de l'application de bureau en un **instrument de performance live autonome**. Il transforme l'animation de marionnettes en une forme d'art tactile et immédiate, à la manière d'un musicien jouant d'un synthétiseur.

L'objectif est de créer un appareil portable, tout-en-un, qui permet à l'artiste de manipuler, d'animer et de "jouer" avec ses marionnettes numériques via des contrôles physiques dédiés, sans jamais toucher une souris ou un clavier.

#### **2. Philosophie de Conception**

*   **Tactile avant tout :** L'interaction doit être physique. Chaque rotation, chaque mouvement doit correspondre à un geste sur un encodeur, un joystick ou un bouton. Le "feeling" est primordial.
*   **Immédiateté :** De l'allumage à l'animation, le processus doit être quasi instantané. L'artiste doit pouvoir exprimer une idée dès qu'elle lui vient.
*   **Portabilité et Autonomie :** L'appareil doit être alimenté par batterie et suffisamment robuste pour être transporté et utilisé n'importe où : sur scène, en atelier, dans un café.
*   **Ouverture et "Hackability" :** Le système doit rester ouvert. L'assignation des contrôles doit être flexible, et l'ajout de nouveaux capteurs ou marionnettes doit être encouragé par la conception.

#### **3. Architecture Matérielle Cible**

Le MACRON-O-TRON 3000 sera un boîtier unique intégrant les composants suivants :

*   **Le Cerveau : Raspberry Pi (Modèle 4 ou 5)**
    *   **Rôle :** Fait tourner l'application PySide6 principale, gère l'affichage et la logique de haut niveau.
    *   **Stockage :** Carte SD ou SSD pour le système d'exploitation et les fichiers d'animation.

*   **Le Panneau de Contrôle : Microcontrôleur (ESP32)**
    *   **Rôle :** Dédié à la lecture en temps réel des capteurs physiques. Il communique avec le Raspberry Pi via une liaison série sans fil (Bluetooth). Cette séparation garantit une réactivité parfaite des contrôles, indépendamment de la charge du Raspberry Pi.
    *   **Composants :**
        *   **Encodeurs Rotatifs (x10-15) :** Pour une rotation fine et infinie des membres (bras, jambes, tête...). Chaque encodeur pourrait avoir un petit écran OLED ou une LED pour indiquer le membre assigné.
        *   **Joystick Analogique (x1) :** Pour le déplacement X/Y du torse de la marionnette.
        *   **Sliders/Faders (x2-4) :** Pour des contrôles additionnels (zoom, paramètres d'effets...).
        *   **Boutons Poussoirs (x10+) :** Pour des actions discrètes : ajouter une keyframe, déclencher une pose prédéfinie, changer de marionnette, etc.

*   **L'Affichage : Écran LCD/OLED (7 à 10 pouces)**
    *   **Rôle :** Affiche l'interface de l'application PySide6. Un écran tactile pourrait permettre des interactions secondaires (sélection de menus, etc.).

*   **Le Châssis et l'Alimentation**
    *   **Boîtier :** Un design sur mesure, potentiellement imprimé en 3D ou découpé au laser, avec une ergonomie pensée pour la performance live.
    *   **Alimentation :** Un pack de batteries LiPo/Li-Ion avec un circuit de charge USB-C pour une autonomie de plusieurs heures.

#### **4. Étapes de Développement (La "Roadmap")**

1.  **Phase 1 : Preuve de Concept (PoC)**
    *   Objectif : Valider la communication de base.
    *   Tâches :
        *   Connecter 1 encodeur rotatif à un ESP32.
        *   Envoyer les données de l'encodeur via Bluetooth SPP à l'application PC.
        *   L'application PC reçoit les données et fait tourner un membre de la marionnette.

2.  **Phase 2 : Prototype "Contrôleur Externe"**
    *   Objectif : Construire un panneau de contrôle fonctionnel, mais toujours connecté au PC.
    *   Tâches :
        *   Construire un boîtier avec plusieurs encodeurs, boutons et un joystick.
        *   Finaliser le protocole de communication.
        *   Développer une interface dans l'application PC pour assigner les contrôles physiques aux membres de la marionnette.

3.  **Phase 3 : Portabilité sur Raspberry Pi**
    *   Objectif : Rendre l'application principale nomade.
    *   Tâches :
        *   Faire tourner l'application PySide6 de manière stable sur un Raspberry Pi avec Raspberry Pi OS.
        *   Gérer la communication Bluetooth directement sur le Pi.
        *   Adapter l'interface pour un écran de plus petite taille.

4.  **Phase 4 : Le MACRON-O-TRON 3000 (Version 1.0)**
    *   Objectif : Assembler le produit final.
    *   Tâches :
        *   Concevoir et fabriquer le boîtier final.
        *   Intégrer le Raspberry Pi, l'écran, le contrôleur ESP32 et la batterie.
        *   Créer un système de démarrage qui lance l'application automatiquement.
