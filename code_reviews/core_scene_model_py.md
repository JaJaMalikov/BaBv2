# Revue de code : core/scene_model.py

## Aperçu
Implémente le modèle de scène : objets, pantins, keyframes et import/export JSON.

## Points positifs
- Structures de données claires (`SceneObject`, `Keyframe`, `SceneModel`).
- Méthodes `to_dict`/`from_dict` facilitant la sérialisation.
- Gestion de la timeline (keyframes, FPS, dimensions de scène).

## Points à améliorer
- La méthode `import_json` contient un appel `self.from_dict(data)` après le bloc `try/except` qui ne sera jamais exécuté.
- Absence de validations lors de l'ajout d'objets ou pantins (doublons, types).
- `SceneObject` pourrait bénéficier d'un `dataclass` pour améliorer la lisibilité.

## Suggestions
- Supprimer ou déplacer l'appel redondant à `self.from_dict` en fin de `import_json`.
- Ajouter des vérifications d'existence lors des insertions pour éviter les collisions de noms.
- Envisager l'utilisation de `dataclasses` et de types plus explicites pour `SceneObject` et `Keyframe`.
