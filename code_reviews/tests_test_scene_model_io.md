# Revue de code: tests/test_scene_model_io.py

## Analyse
Vérifie la sérialisation/désérialisation des objets et de la scène ainsi que la robustesse face à des fichiers JSON invalides ou mal structurés.

## Recommandations
- Ajouter les imports manquants (`SceneModel`, `SceneObject`) pour clarifier les dépendances.
- Tester des cas supplémentaires comme l'import de scènes avec keyframes multiples ou des objets attachés.
- Utiliser `pytest.mark.parametrize` pour couvrir plusieurs structures invalides.
