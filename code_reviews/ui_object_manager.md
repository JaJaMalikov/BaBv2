# Revue de code: ui/object_manager.py

## Analyse
Centralise la création, duplication, suppression et mise à l'échelle des pantins et objets de la scène. Gère également la capture d'état pour les keyframes.

## Recommandations
- Le fichier est volumineux ; envisager de séparer la gestion des pantins et des objets dans des classes distinctes.
- Introduire des exceptions spécifiques plutôt que des `return` silencieux pour faciliter le débogage.
- Documenter les effets secondaires des méthodes (mise à jour de l'UI, manipulations du modèle).
- Ajouter des tests unitaires couvrant l'ajout/duplication/suppression et l'attachement d'objets.
