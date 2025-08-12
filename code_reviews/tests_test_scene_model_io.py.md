# Revue de code : tests/test_scene_model_io.py

## Aperçu
Tests unitaires pour la sérialisation et désérialisation du `SceneModel` et des `SceneObject`.

## Points forts
- Couvre à la fois la conversion `to_dict`/`from_dict` et l'export/import JSON.
- Utilise un répertoire temporaire fourni par `pytest` pour l'I/O.

## Points à améliorer
- Les assertions ne vérifient pas les erreurs de lecture/écriture (fichier manquant, permissions).
- Pas de test négatif pour les données JSON corrompues.

## Recommandations
1. Ajouter un test pour s'assurer qu'une erreur est levée lors de la lecture d'un JSON invalide.
2. Vérifier que la fonction `export_json` crée effectivement le fichier avec le contenu attendu.
