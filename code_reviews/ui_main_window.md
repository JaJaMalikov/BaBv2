# Revue de code: ui/main_window.py

## Analyse
Contrôleur principal de l'application reliant modèle et interface : initialise la scène, gère les docks, connecte les signaux et orchestre les différentes composantes (timeline, overlays, playback, etc.).

## Recommandations
- Le fichier est très volumineux ; envisager de déléguer certaines sections (gestion des overlays, configuration initiale) à des classes utilitaires.
- Ajouter des annotations de type plus précises pour clarifier les attributs utilisés.
- Renforcer la gestion des erreurs lors de l'initialisation de la fenêtre et du chargement des paramètres.
- Introduire des tests d'intégration ciblés pour vérifier la connexion des signaux critiques.
