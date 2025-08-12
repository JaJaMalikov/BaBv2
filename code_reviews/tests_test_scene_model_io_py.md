# Revue de code : tests/test_scene_model_io.py

## Aperçu
Tests unitaires pour la sérialisation/désérialisation des objets de scène.

## Points positifs
- Couvre la conversion `SceneObject` -> dict -> `SceneObject`.
- Vérifie l'export/import JSON d'une scène simple.

## Points à améliorer
- Les assertions pourraient vérifier les champs `attached_to` après import.
- Pas de test pour les erreurs de lecture/écriture.

## Suggestions
- Ajouter un test pour le cas où le fichier JSON est corrompu ou manquant.
- Introduire des `pytest.mark.parametrize` pour couvrir plusieurs types d'objets.
