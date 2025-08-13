# Revue de code: ui/scene_visuals.py

## Analyse
Responsable de l'affichage visuel global de la scène: bordure, dimensions et image d'arrière‑plan.

## Recommandations
- Utiliser des signaux/slots pour notifier `MainWindow` des changements de dimensions après chargement d'une image.
- Centraliser les couleurs/largeurs de traits pour harmoniser le thème.
- Ajouter un mécanisme de mise à l'échelle optionnel pour les grandes images d'arrière‑plan.
- Couvrir la gestion d'erreurs de `update_background` par des tests.
