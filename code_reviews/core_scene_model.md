# Code Review : core/scene_model.py

## Points positifs
- Modèle de scène structuré avec classes `SceneObject` et `Keyframe` clairement définies.
- Méthodes d'import/export JSON permettant la persistance de l'état.
- Utilisation de `logging` pour signaler les erreurs lors du chargement.

## Points d'amélioration
- De nombreuses méthodes manquent de docstrings détaillant les paramètres et valeurs de retour.
- La méthode `import_json` contient un appel `self.from_dict(data)` après un `return False`, code mort à corriger.
- Les attributs de `SceneModel` ne sont pas typés; l'introduction de `Dict[str, SceneObject]` etc. clarifierait le modèle.
- `add_keyframe` mélange la capture d'état et la gestion de la structure; séparer ces responsabilités.

## Recommandations
- Ajouter des annotations de type et docstrings pour toutes les méthodes publiques.
- Corriger la structure de `import_json` pour éviter le code inatteignable et retourner explicitement le succès.
- Envisager l'utilisation de dataclasses pour `SceneObject` et `Keyframe` afin de réduire le code boilerplate.
- Couvrir l'import/export avec des tests supplémentaires (ex : valeurs de `background_path`).
