# Revue de code : core/scene_model.py

## Aperçu
Modèle de scène central gérant les objets, les pantins et la timeline (keyframes, paramètres de scène, import/export JSON).

## Points forts
- Structure claire des entités `SceneObject`, `Keyframe` et `SceneModel`.
- Méthodes `to_dict`/`from_dict` facilitant la sérialisation.

## Points à améliorer
- `import_json` contient du code inatteignable (`self.from_dict(data)` après un `return`).
- Manque de type hints pour certaines méthodes (ex. `add_puppet` sans type de retour explicite).
- Gestion d'erreurs minimale lors de l'attache/détache d'objets.

## Recommandations
1. Corriger l'instruction inatteignable dans `import_json` et renforcer la gestion d'erreurs.
2. Ajouter des annotations de types et des docstrings pour toutes les méthodes publiques.
3. Envisager de séparer la logique de sérialisation dans un module dédié pour alléger la classe.
