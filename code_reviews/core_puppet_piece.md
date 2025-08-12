# Code Review : core/puppet_piece.py

## Points positifs
- Gestion précise des poignées de rotation et de pivot avec mise à jour automatique.
- Utilisation de types `Optional` et `List` pour clarifier les attributs.
- Séparation entre `RotationHandle` et `PivotHandle` pour une meilleure lisibilité.

## Points d'amélioration
- Peu de docstrings expliquant le rôle des classes et méthodes.
- Certains imports (ex. `Any`) sont génériques; l'utilisation de types plus précis améliorerait la maintenabilité.
- Les constantes de couleurs pourraient être centralisées pour assurer la cohérence du thème.
- La logique de calcul d'angles se répète dans les événements de souris; extraire une méthode utilitaire.

## Recommandations
- Ajouter des docstrings détaillant les interactions des poignées avec la scène.
- Introduire des annotations de type complètes, notamment pour les valeurs de retour.
- Factoriser la logique commune des événements pour faciliter les futurs changements.
- Ajouter des tests unitaires ciblant `rotate_piece` et `update_transform_from_parent`.
