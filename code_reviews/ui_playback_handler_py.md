# Revue de code : ui/playback_handler.py

## Aperçu
Gère la lecture de l'animation, la navigation dans les frames et la synchronisation avec la timeline.

## Points positifs
- Séparation claire de la logique de playback hors de `MainWindow`.
- Utilisation des signaux Qt pour communiquer avec la timeline et l'inspecteur.
- Méthodes compactes et lisibles.

## Points à améliorer
- Manque de docstrings ou commentaires détaillant le rôle de chaque méthode.
- Certains paramètres pourraient bénéficier de types plus précis (ex: `go_to_frame`).
- Pas de gestion d'état pour éviter les appels multiples à `play_animation`.

## Suggestions
- Ajouter une documentation de classe et des commentaires sur les signaux émis.
- Valider les entrées (FPS positif, plages de frames cohérentes).
- Introduire éventuellement un état "en lecture" pour éviter les doubles démarrages du timer.
