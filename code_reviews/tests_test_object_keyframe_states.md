# Revue de code: tests/test_object_keyframe_states.py

## Analyse
Test d'intégration vérifiant que les objets conservent un état distinct par keyframe, incluant l'attachement/détachement et les positions locales ou globales.

## Recommandations
- Utiliser des fixtures pour créer et détruire `MainWindow` afin de limiter les effets de bord.
- Compléter avec des assertions sur la rotation/scale pour une couverture complète de l'état.
- Ajouter des tests de régression pour des objets multiples ou des keyframes non consécutifs.
