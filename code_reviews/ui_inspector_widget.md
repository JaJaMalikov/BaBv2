# Code Review : ui/inspector_widget.py

## Points positifs
- Interface complète pour gérer objets et pantins via une liste et divers contrôles.
- Bonne utilisation des signaux Qt pour synchroniser l'UI avec le modèle.
- Structure claire des layouts avec séparateurs pour améliorer l'ergonomie.

## Points d'amélioration
- Fichier volumineux combinant création de widgets, callbacks et logique métier; la lisibilité en souffre.
- Plusieurs méthodes privées n'ont pas d'annotations de type ni de docstrings.
- La fonction `_attached_state_for_frame` contient des variables peu explicites (`si`, `prev`), rendant la logique difficile à suivre.
- Aucune gestion d'erreur lors de l'accès aux structures du modèle (`get` sans vérification de retour).

## Recommandations
- Scinder certaines parties (par ex. gestion des attachments) dans des helpers dédiés.
- Ajouter des docstrings et annotations de type pour les méthodes privées.
- Renommer les variables pour refléter leur rôle et commenter les sections complexes.
- Envisager des tests d'intégration pour garantir la synchronisation UI ↔ modèle.
