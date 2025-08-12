# Revue de code : ui/inspector_widget.py

## Aperçu
Inspector permettant de sélectionner, modifier et attacher des objets ou pantins via une interface simple.

## Points forts
- Interface structurée avec `QFormLayout` et actions dédiées (dupliquer, supprimer, attacher).
- Rafraîchissement dynamique des listes en fonction du modèle de scène.

## Points à améliorer
- Fichier volumineux combinant interface, logique de sélection et manipulation d'objets.
- Certaines fonctions retournent `None` ou `tuple` sans annotation explicite.
- Absence de messages d'erreur utilisateur lorsque les opérations échouent.

## Recommandations
1. Séparer la logique de mise à jour du modèle dans une classe/service dédié.
2. Ajouter des annotations de types et des docstrings pour les méthodes `_on_*`.
3. Informer l'utilisateur via des `QMessageBox` ou logs visibles en cas d'erreur d'attache/détache.
