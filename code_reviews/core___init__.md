# Revue de code: core/__init__.py

## Analyse
Expose les principales classes du domaine (`SceneModel`, `Puppet`, etc.) pour faciliter les imports externes.

## Recommandations
- Vérifier la pertinence de l'export de toutes les classes pour éviter de figer l'API publique.
- Ajouter une documentation globale décrivant la responsabilité du package `core`.
- Mettre à jour `__all__` lors de l'ajout de nouvelles entités pour conserver la cohérence.
