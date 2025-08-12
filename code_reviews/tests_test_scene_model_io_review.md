# Revue de code : tests/test_scene_model_io.py

## Observations Générales
- Tests unitaires simples couvrant la sérialisation et l'export/import du modèle de scène.
- Bon usage de `tmp_path` pour les opérations fichier.

## Points Positifs
- Vérifie le round-trip `SceneObject.to_dict` -> `from_dict`.
- Teste la persistance via `export_json` et `import_json`.

## Problèmes Identifiés
1. Aucun test pour les erreurs possibles (fichier corrompu, attribut manquant, etc.).
2. Absence de docstrings pour expliquer la finalité de chaque test.
3. Les assertions pourraient être regroupées ou factorisées pour réduire la duplication.

## Recommandations
- Ajouter des cas de tests négatifs pour vérifier la robustesse de `import_json`.
- Introduire des commentaires/docstrings pour clarifier l'intention de chaque test.
- Utiliser des helpers ou fixtures pour créer des objets `SceneObject` réutilisables.
