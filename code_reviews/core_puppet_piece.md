# Revue de code: core/puppet_piece.py

## Analyse
Implémente les éléments graphiques représentant les membres du pantin ainsi que les poignées de rotation et de pivot pour l'édition dans la scène.

## Recommandations
- Centraliser les constantes de taille/couleur afin de faciliter leur personnalisation.
- Séparer la logique d'interaction des objets graphiques pour alléger `PuppetPiece`.
- Ajouter des tests unitaires pour les calculs d'angles et de pivots.
- Documenter la responsabilité des classes `RotationHandle` et `PivotHandle`.
