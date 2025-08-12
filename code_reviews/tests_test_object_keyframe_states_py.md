# Revue de code : tests/test_object_keyframe_states.py

## Aperçu
Test d'intégration vérifiant la persistance des états d'un objet attaché/détaché à différents keyframes.

## Points positifs
- Reproduit un scénario complet de création, attache, détache et vérifie la synchronisation modèle/vue.
- Utilise `pytest` et un fixture `app` pour l'initialisation Qt.

## Points à améliorer
- Ajout de `sys.path` dans le test, pouvant masquer des problèmes d'importation.
- Test relativement long et dépendant des assets présents dans le repo.

## Suggestions
- Utiliser des modules de test installables ou des paquets pour éviter la modification de `sys.path`.
- Scinder le scénario en plusieurs tests plus ciblés (attache, détache, snapshot).
- Ajouter des assertions sur l'état du modèle après la lecture d'une scène sauvegardée.
