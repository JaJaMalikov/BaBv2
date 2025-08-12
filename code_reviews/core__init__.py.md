# Revue de code : core/__init__.py

## Aperçu
Expose les modèles et utilitaires principaux du cœur de l'application.

## Points forts
- Interface explicite via `__all__` facilitant l'import sélectif.
- Documentation succincte en en-tête.

## Points à améliorer
- Absence de vérification lors de l'import; une erreur de dépendance pourrait rester silencieuse.

## Recommandations
1. Ajouter des tests d'import automatique pour prévenir les régressions.
2. Compléter la documentation pour décrire rapidement chaque élément exporté.
