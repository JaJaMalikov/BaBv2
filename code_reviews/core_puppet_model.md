# Revue de code: core/puppet_model.py

## Analyse
Définit les structures de données statiques décrivant la hiérarchie d'un pantin et fournit des utilitaires pour construire les membres à partir d'un SVG.

## Recommandations
- Remplacer les dictionnaires globaux par des configurations externes ou des constantes structurées pour faciliter la personnalisation.
- Introduire des `dataclasses` pour `PuppetMember` afin de clarifier les attributs.
- Ajouter des vérifications d'erreurs lors du chargement des groupes SVG.
- Documenter le format attendu des fichiers SVG et des cartes `PARENT_MAP`/`PIVOT_MAP`.
