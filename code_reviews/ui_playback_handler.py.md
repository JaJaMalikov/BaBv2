# Revue de code : ui/playback_handler.py

## Aperçu
Gestionnaire de lecture qui coordonne timeline, modèle de scène et synchronisation de l'inspecteur.

## Points forts
- Responsabilités bien isolées hors de `MainWindow`.
- Utilise des signaux pour demander des snapshots ou l'ajout de keyframes.
- Méthodes courtes et ciblées.

## Points à améliorer
- `next_frame` contient une logique un peu dense (calcul du nouveau frame, boucle). 
- L'objet ne gère pas l'arrêt automatique lorsque la scène ne contient aucun keyframe.

## Recommandations
1. Extraire la logique de calcul de la prochaine frame dans une méthode privée pour simplifier `next_frame`.
2. Vérifier l'existence de keyframes avant de lancer la lecture pour éviter les boucles vides.
