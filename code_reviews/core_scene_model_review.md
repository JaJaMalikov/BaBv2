# Revue de code : core/scene_model.py

## Observations Générales
- Définit les classes `SceneObject`, `Keyframe` et `SceneModel` avec une structure claire.
- Sérialisation JSON prévue via `to_dict`/`from_dict` et `export_json`/`import_json`.
- Présence de commentaires utiles mais peu de docstrings détaillées sur les méthodes.

## Points Positifs
- Utilisation de `typing` pour améliorer la lisibilité et la robustesse.
- Tri des keyframes après insertion assurant l'ordre chronologique.

## Problèmes Identifiés
1. Import `logging` utilisé uniquement dans `import_json` ; vérifier qu'une configuration de logging existe ailleurs.
2. Méthode `import_json` contient une ligne `self.from_dict(data)` après le `return False`, code mort à supprimer.
3. Manque de validations sur les valeurs (ex. type de `index`, existence des clés) lors de la désérialisation.
4. Peu ou pas de tests unitaires associés aux objets `SceneObject`.

## Recommandations
- Ajouter des docstrings aux méthodes principales pour clarifier leur usage.
- Introduire des exceptions spécifiques ou des retours d'erreur détaillés pour l'import/export.
- Élargir la couverture de tests pour la sérialisation des `SceneObject` et la gestion des keyframes.
