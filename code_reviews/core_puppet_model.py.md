# Revue de code : core/puppet_model.py

## Aperçu
Définit la structure hiérarchique d'un pantin 2D, ses pivots, l'ordre d'affichage et la construction depuis un SVG.

## Points forts
- Utilisation de dictionnaires (`PARENT_MAP`, `PIVOT_MAP`, `Z_ORDER`) pour configurer la hiérarchie.
- Méthodes utilitaires comme `compute_child_map` et `validate_svg_structure` aidant au debug.

## Points à améliorer
- Les données de configuration sont en variables globales difficiles à maintenir si plusieurs pantins sont nécessaires.
- La classe `Puppet` mélange construction, validation et debug (`main()`).
- Manque de commentaires/docstrings sur plusieurs méthodes critiques.

## Recommandations
1. Encapsuler les constantes de configuration dans une classe ou un fichier JSON pour faciliter la personnalisation.
2. Séparer les fonctions de debug (`main`, `validate_svg_structure`) du module principal.
3. Ajouter des docstrings détaillant les algorithmes de calcul des pivots et de la hiérarchie.
