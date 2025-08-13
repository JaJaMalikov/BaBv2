# Revue de code: core/scene_model.py

## Analyse
Modélise les objets de la scène, les pantins et les keyframes. Fournit des méthodes de sérialisation JSON et de validation des données.

## Recommandations
- Envisager l'utilisation de `dataclasses` pour `SceneObject` et `Keyframe` afin de réduire le code boilerplate.
- Documenter davantage les méthodes publiques, notamment `to_dict` et `from_dict`.
- Factoriser la validation JSON pour permettre une extension plus aisée.
- Ajouter des tests couvrant les cas limites d'import/export.
