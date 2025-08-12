# Code Review : ui/scene_io.py

## Points positifs
- Fonctions séparées pour sauvegarder, charger, exporter et importer la scène.
- Utilisation du modèle pour récupérer l'état (`scene_model.to_dict`).
- Gestion basique des erreurs via `logging` lors de l'export.

## Points d'amélioration
- L'import de `logging` est placé en milieu de fichier, ce qui n'est pas conventionnel.
- Les fonctions `save_scene` et `load_scene` n'ont pas de gestion d'erreur si l'utilisateur annule la boîte de dialogue.
- `import_scene` contient un bloc `try/except` très large où les exceptions sont simplement affichées; l'état du programme peut rester incohérent.
- Manque de docstrings pour `create_blank_scene` et absence d'annotations de type de retour.

## Recommandations
- Déplacer l'import de `logging` en haut du fichier et structurer les `try/except` pour traiter les erreurs spécifiques.
- Retourner un booléen indiquant le succès des opérations pour faciliter les tests.
- Ajouter des annotations de type et des docstrings pour tous les helpers.
- Externaliser certaines responsabilités (reconstruction de la scène) dans des services dédiés pour réduire la taille de `import_scene`.
