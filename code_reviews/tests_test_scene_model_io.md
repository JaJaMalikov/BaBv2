# Code Review : tests/test_scene_model_io.py

## Points positifs
- Couvre la sérialisation/desérialisation d'un `SceneObject` et le cycle complet d'export/import de `SceneModel`.
- Utilisation de `tmp_path` de pytest pour gérer les fichiers temporaires.

## Points d'amélioration
- Les tests ne vérifient pas l'export des `puppets` ni des paramètres de scène (taille, fps...).
- Absence de tests négatifs (fichier corrompu, valeurs manquantes) pour valider la robustesse.

## Recommandations
- Ajouter des assertions sur les champs `background_path` et sur la liste des puppets exportés.
- Tester l'import de fichiers invalides pour s'assurer que `SceneModel.import_json` gère correctement les erreurs.
