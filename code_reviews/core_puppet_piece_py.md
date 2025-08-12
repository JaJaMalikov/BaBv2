# Revue de code : core/puppet_piece.py

## Aperçu
Gère la représentation graphique d'un membre de pantin, avec gestion des pivots, poignées de rotation et propagation des transformations.

## Points positifs
- Architecture claire `PuppetPiece`/`RotationHandle`/`PivotHandle`.
- Mise à jour récursive des transformations pour synchroniser parents et enfants.
- Utilisation de couleurs distinctes pour différencier les membres gauche/droite.

## Points à améliorer
- Taille du fichier importante et méthodes longues, rendant la lecture plus difficile.
- Plusieurs `if` imbriqués dans `update_transform_from_parent` et `rotate_piece`; possibilité de factoriser.
- Certains attributs comme `handle_local_pos` sont conditionnellement définis, ce qui peut mener à des erreurs si mal utilisé.

## Suggestions
- Scinder certaines responsabilités (gestion des poignées, géométrie) dans des classes ou fonctions utilitaires.
- Ajouter des annotations de type plus précises et des docstrings pour les méthodes clés.
- Envisager d'utiliser des propriétés pour exposer `local_rotation` ou lier automatiquement la mise à jour des poignées.
