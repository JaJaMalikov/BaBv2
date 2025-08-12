# Revue de code : core/__init__.py

## Observations Générales
- Fournit un point d'entrée clair pour les modèles et helpers du domaine.
- La docstring résume succinctement le module.
- L'utilisation de `__all__` facilite l'import sélectif.

## Recommandations
1. Vérifier que l'import de tous les éléments exposés est réellement nécessaire pour éviter les dépendances circulaires.
2. Envisager d'ajouter des commentaires ou docstrings supplémentaires pour expliquer les principaux objets exportés.
