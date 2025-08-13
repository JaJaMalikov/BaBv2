# Revue de code: ui/inspector_widget.py

## Analyse
Widget d'inspection permettant de lister les objets/pantins et de modifier leurs propriétés (échelle, rotation, z‑order, attachements). Appelle directement des méthodes du `MainWindow`.

## Recommandations
- Séparer la gestion des objets et des pantins en composants distincts pour clarifier les responsabilités.
- Ajouter des docstrings aux callbacks privés (`_on_item_changed`, etc.) afin d'expliciter leur rôle.
- Factoriser la logique de sélection et d'attachement pour éviter la duplication de code.
- Tester les cas de suppression/duplication et d'attache/détache pour assurer la cohérence du modèle.
